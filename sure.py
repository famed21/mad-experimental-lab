import curses
from curses import wrapper
import math

class SureBettingSystem:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.matches = []
        self.current_menu = "main"
        self.current_match = 0
        curses.curs_set(1)  # Show cursor
        self.init_colors()
        self.run()

    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def draw_menu(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        
        if self.current_menu == "main":
            title = "Sure Betting Arbitrage System"
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
            
            menu_items = [
                "1. Add New Match",
                "2. View All Matches",
                "3. Calculate Arbitrage",
                "4. Clear All Matches",
                "5. Exit"
            ]
            
            for idx, item in enumerate(menu_items, start=3):
                self.stdscr.addstr(idx, w//2 - len(item)//2, item)
            
            self.stdscr.addstr(h-2, 2, "Select an option (1-5): ", curses.color_pair(3))
        
        elif self.current_menu == "add_match":
            self.draw_add_match_screen()
        
        elif self.current_menu == "view_matches":
            self.draw_view_matches_screen()
        
        elif self.current_menu == "calculate":
            self.draw_calculate_screen()
        
        self.stdscr.refresh()

    def draw_add_match_screen(self):
        h, w = self.stdscr.getmaxyx()
        title = "Add New Match"
        self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        
        questions = [
            f"Match {len(self.matches)+1} Details",
            "Team A Name: ",
            "Team A Odds: ",
            "Team B Name: ",
            "Team B Odds: ",
            "Include Draw? (y/n): "
        ]
        
        for idx, question in enumerate(questions, start=3):
            self.stdscr.addstr(idx, 2, question)
        
        self.stdscr.refresh()

    def draw_view_matches_screen(self):
        h, w = self.stdscr.getmaxyx()
        title = "View All Matches"
        self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        
        if not self.matches:
            self.stdscr.addstr(3, 2, "No matches added yet!", curses.color_pair(2))
        else:
            for idx, match in enumerate(self.matches, start=3):
                match_str = f"Match {idx-2}: {match['team_a']['name']} ({match['team_a']['odds']}) vs {match['team_b']['name']} ({match['team_b']['odds']})"
                if match.get('draw'):
                    match_str += f" | Draw ({match['draw']['odds']})"
                self.stdscr.addstr(idx, 2, match_str)
        
        self.stdscr.addstr(h-2, 2, "Press any key to return...", curses.color_pair(3))

    def draw_calculate_screen(self):
        h, w = self.stdscr.getmaxyx()
        title = "Calculate Arbitrage"
        self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        
        if not self.matches:
            self.stdscr.addstr(3, 2, "No matches to calculate!", curses.color_pair(2))
            self.stdscr.addstr(h-2, 2, "Press any key to return...", curses.color_pair(3))
            return
        
        self.stdscr.addstr(3, 2, "Enter total stake amount: ")
        self.stdscr.refresh()
        
        # Get stake amount
        curses.echo()
        stake_str = self.stdscr.getstr(3, 25).decode('utf-8')
        curses.noecho()
        
        try:
            total_stake = float(stake_str)
        except ValueError:
            self.stdscr.addstr(5, 2, "Invalid stake amount!", curses.color_pair(2))
            self.stdscr.addstr(h-2, 2, "Press any key to return...", curses.color_pair(3))
            return
        
        # Calculate for each match
        for idx, match in enumerate(self.matches, start=5):
            if match.get('draw'):
                odds = [match['team_a']['odds'], match['team_b']['odds'], match['draw']['odds']]
            else:
                odds = [match['team_a']['odds'], match['team_b']['odds']]
            
            result = self.calculate_arbitrage(odds, total_stake)
            
            if result:
                match_title = f"{match['team_a']['name']} vs {match['team_b']['name']}:"
                self.stdscr.addstr(idx, 2, match_title, curses.color_pair(4))
                
                self.stdscr.addstr(idx+1, 4, f"Stake on {match['team_a']['name']}: ${result['stakes'][0]:.2f}")
                self.stdscr.addstr(idx+2, 4, f"Stake on {match['team_b']['name']}: ${result['stakes'][1]:.2f}")
                if match.get('draw'):
                    self.stdscr.addstr(idx+3, 4, f"Stake on Draw: ${result['stakes'][2]:.2f}")
                
                self.stdscr.addstr(idx+4, 4, f"Guaranteed Profit: ${result['guaranteed_profit']:.2f}", curses.color_pair(1))
                self.stdscr.addstr(idx+5, 4, f"Profit if {match['team_a']['name']} wins: ${result['profits'][0]:.2f}")
                self.stdscr.addstr(idx+6, 4, f"Profit if {match['team_b']['name']} wins: ${result['profits'][1]:.2f}")
                if match.get('draw'):
                    self.stdscr.addstr(idx+7, 4, f"Profit if Draw: ${result['profits'][2]:.2f}")
                
                idx += 9
            else:
                self.stdscr.addstr(idx, 2, f"No arbitrage opportunity for {match['team_a']['name']} vs {match['team_b']['name']}", curses.color_pair(2))
                idx += 2
        
        self.stdscr.addstr(h-2, 2, "Press any key to return...", curses.color_pair(3))

    def calculate_arbitrage(self, odds_list, total_stake):
        probabilities = [1/odd for odd in odds_list]
        total_prob = sum(probabilities)
        
        if total_prob >= 1:
            return None  # No arbitrage opportunity
        
        # Calculate stakes for each outcome
        stakes = [(total_stake * p) / total_prob for p in probabilities]
        
        # Calculate profits for each outcome
        profits = [(stakes[i] * odds_list[i] - total_stake) for i in range(len(odds_list))]
        
        return {
            'stakes': stakes,
            'profits': profits,
            'guaranteed_profit': (total_stake / total_prob) - total_stake
        }

    def add_match(self):
        self.current_menu = "add_match"
        self.draw_menu()
        
        h, w = self.stdscr.getmaxyx()
        curses.echo()
        
        # Get team A name
        self.stdscr.addstr(4, 15, " " * 30)  # Clear space
        team_a = self.stdscr.getstr(4, 15).decode('utf-8')
        
        # Get team A odds
        self.stdscr.addstr(5, 15, " " * 10)
        odds_a_str = self.stdscr.getstr(5, 15).decode('utf-8')
        try:
            odds_a = float(odds_a_str)
        except ValueError:
            self.stdscr.addstr(7, 2, "Invalid odds format!", curses.color_pair(2))
            self.stdscr.getch()
            curses.noecho()
            self.current_menu = "main"
            return
        
        # Get team B name
        self.stdscr.addstr(6, 15, " " * 30)
        team_b = self.stdscr.getstr(6, 15).decode('utf-8')
        
        # Get team B odds
        self.stdscr.addstr(7, 15, " " * 10)
        odds_b_str = self.stdscr.getstr(7, 15).decode('utf-8')
        try:
            odds_b = float(odds_b_str)
        except ValueError:
            self.stdscr.addstr(9, 2, "Invalid odds format!", curses.color_pair(2))
            self.stdscr.getch()
            curses.noecho()
            self.current_menu = "main"
            return
        
        # Get draw option
        self.stdscr.addstr(8, 18, " " * 3)
        include_draw = self.stdscr.getstr(8, 18).decode('utf-8').lower() == 'y'
        
        draw_odds = None
        if include_draw:
            self.stdscr.addstr(9, 15, " " * 10)
            self.stdscr.addstr(9, 2, "Enter Draw Odds: ")
            draw_odds_str = self.stdscr.getstr(9, 18).decode('utf-8')
            try:
                draw_odds = float(draw_odds_str)
            except ValueError:
                self.stdscr.addstr(11, 2, "Invalid odds format!", curses.color_pair(2))
                self.stdscr.getch()
                curses.noecho()
                self.current_menu = "main"
                return
        
        # Add match to list
        match_data = {
            'team_a': {'name': team_a, 'odds': odds_a},
            'team_b': {'name': team_b, 'odds': odds_b}
        }
        if include_draw:
            match_data['draw'] = {'odds': draw_odds}
        
        self.matches.append(match_data)
        
        curses.noecho()
        self.current_menu = "main"

    def run(self):
        while True:
            self.draw_menu()
            
            if self.current_menu == "main":
                key = self.stdscr.getch()
                if key == ord('1'):
                    self.add_match()
                elif key == ord('2'):
                    self.current_menu = "view_matches"
                elif key == ord('3'):
                    self.current_menu = "calculate"
                elif key == ord('4'):
                    self.matches = []
                elif key == ord('5'):
                    break
            
            elif self.current_menu in ["view_matches", "calculate"]:
                self.stdscr.getch()
                self.current_menu = "main"

def main(stdscr):
    SureBettingSystem(stdscr)

if __name__ == "__main__":
    wrapper(main)
