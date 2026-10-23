import curses
from curses import wrapper
import json
import os
import math
import time
from datetime import datetime

class SureBettingSystem:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.matches = []
        self.history = []
        self.current_menu = "main"
        self.selected_option = 0
        self.blink_state = True
        self.last_redraw = 0
        curses.curs_set(0)
        self.init_colors()
        self.load_history()
        self.run()

    def init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(6, curses.COLOR_BLUE, curses.COLOR_BLACK)

    def draw_border(self, h, w):
        self.stdscr.attron(curses.color_pair(6))
        try:
            self.stdscr.border()
        except curses.error:
            pass
        self.stdscr.attroff(curses.color_pair(6))

    def draw_ascii_bar(self, value, max_value, width, char='█'):
        if max_value == 0:
            return ""
        bar_length = int((value / max_value) * width)
        return char * max(bar_length, 1)

    def draw_ascii_pie(self, values, width):
        total = sum(values)
        if total == 0:
            return ["Empty", ""]
        segments = []
        percentages = []
        chars = ['█', '▒', '░']
        for i, value in enumerate(values):
            percentage = (value / total) * 100
            segment_length = int((percentage / 100) * width)
            segments.append(chars[i % len(chars)] * max(segment_length, 1))
            percentages.append(f"{percentage:.1f}%")
        return ["".join(segments), ", ".join(percentages)]

    def load_history(self):
        try:
            if os.path.exists("betting_history.json"):
                with open("betting_history.json", "r") as f:
                    self.history = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.history = []

    def save_history(self):
        try:
            with open("betting_history.json", "w") as f:
                json.dump(self.history, f, indent=2)
        except IOError:
            pass

    def draw_menu(self):
        h, w = self.stdscr.getmaxyx()
        current_time = time.time() * 1000

        if self.current_menu == "main":
            if self.last_redraw == 0:
                self.stdscr.clear()
                self.draw_border(h, w)
                header = "❄ Cold Fingers Betting System ❄"
                footer = "Use ↑↓ or 1-6 to select, Enter to confirm"
                try:
                    self.stdscr.addstr(1, w//2 - len(header)//2, header, curses.color_pair(1) | curses.A_BOLD)
                    self.stdscr.addstr(h-2, w//2 - len(footer)//2, footer, curses.color_pair(4))
                except curses.error:
                    pass

            menu_items = [
                "1. Add New Match",
                "2. View All Matches",
                "3. Calculate Arbitrage",
                "4. View History",
                "5. Clear All Matches",
                "6. Exit"
            ]

            if (current_time - self.last_redraw) > 500:
                self.blink_state = not self.blink_state
                self.last_redraw = current_time

            for idx, item in enumerate(menu_items, start=3):
                x_pos = w//2 - len(item)//2
                try:
                    if idx - 3 == self.selected_option:
                        attr = curses.color_pair(5) | curses.A_BOLD
                        self.stdscr.addstr(idx, x_pos, item, attr)
                    else:
                        self.stdscr.addstr(idx, x_pos, item, curses.color_pair(3))
                except curses.error:
                    pass

        elif self.current_menu == "add_match":
            self.draw_add_match_screen()
        
        elif self.current_menu == "view_matches":
            self.draw_view_matches_screen()
        
        elif self.current_menu == "calculate":
            self.draw_calculate_screen()
        
        elif self.current_menu == "history":
            self.draw_history_screen()
        
        self.stdscr.refresh()

    def draw_add_match_screen(self):
        h, w = self.stdscr.getmaxyx()
        self.draw_border(h, w)
        title = "❄ Add New Match ❄"
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        
        questions = [
            f"Match {len(self.matches)+1} Details",
            "Team A Name: ",
            "Team A Odds: ",
            "Team B Name: ",
            "Team B Odds: ",
            "Include Draw? (y/n): "
        ]
        
        for idx, question in enumerate(questions, start=3):
            try:
                self.stdscr.addstr(idx, 4, question, curses.color_pair(3))
            except curses.error:
                pass
        
        self.stdscr.refresh()

    def get_user_input(self, y, x, prompt, default=""):
        curses.echo()
        self.stdscr.addstr(y, x, " " * 20)
        self.stdscr.move(y, x)
        self.stdscr.refresh()
        try:
            user_input = self.stdscr.getstr().decode('utf-8').strip() or default
        except curses.error:
            user_input = default
        curses.noecho()
        return user_input

    def add_match(self):
        self.current_menu = "add_match"
        self.draw_menu()
        
        h, w = self.stdscr.getmaxyx()
        
        team_a = self.get_user_input(4, 16, "Team A Name")
        if not team_a:
            try:
                self.stdscr.addstr(10, 4, "Team name cannot be empty!", curses.color_pair(2))
                self.stdscr.getch()
            except curses.error:
                pass
            self.current_menu = "main"
            return
        
        odds_a_str = self.get_user_input(5, 16, "Team A Odds")
        try:
            odds_a = float(odds_a_str)
            if odds_a <= 1:
                raise ValueError("Odds must be greater than 1")
        except ValueError:
            try:
                self.stdscr.addstr(10, 4, "Invalid odds format!", curses.color_pair(2))
                self.stdscr.getch()
            except curses.error:
                pass
            self.current_menu = "main"
            return
        
        team_b = self.get_user_input(6, 16, "Team B Name")
        if not team_b:
            try:
                self.stdscr.addstr(10, 4, "Team name cannot be empty!", curses.color_pair(2))
                self.stdscr.getch()
            except curses.error:
                pass
            self.current_menu = "main"
            return
        
        odds_b_str = self.get_user_input(7, 16, "Team B Odds")
        try:
            odds_b = float(odds_b_str)
            if odds_b <= 1:
                raise ValueError("Odds must be greater than 1")
        except ValueError:
            try:
                self.stdscr.addstr(10, 4, "Invalid odds format!", curses.color_pair(2))
                self.stdscr.getch()
            except curses.error:
                pass
            self.current_menu = "main"
            return
        
        include_draw = self.get_user_input(8, 20, "Include Draw").lower() == 'y'
        
        draw_odds = None
        if include_draw:
            draw_odds_str = self.get_user_input(9, 20, "Draw Odds")
            try:
                draw_odds = float(draw_odds_str)
                if draw_odds <= 1:
                    raise ValueError("Odds must be greater than 1")
            except ValueError:
                try:
                    self.stdscr.addstr(11, 4, "Invalid odds format!", curses.color_pair(2))
                    self.stdscr.getch()
                except curses.error:
                    pass
                self.current_menu = "main"
                return
        
        match_data = {
            'team_a': {'name': team_a, 'odds': odds_a},
            'team_b': {'name': team_b, 'odds': odds_b}
        }
        if include_draw:
            match_data['draw'] = {'odds': draw_odds}
        
        self.matches.append(match_data)
        try:
            self.stdscr.addstr(10, 4, "Match added successfully!", curses.color_pair(1))
            self.stdscr.getch()
        except curses.error:
            pass
        self.current_menu = "main"

    def draw_view_matches_screen(self):
        h, w = self.stdscr.getmaxyx()
        self.draw_border(h, w)
        title = "❄ View All Matches ❄"
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        
        if not self.matches:
            try:
                self.stdscr.addstr(4, 4, "No matches added yet!", curses.color_pair(2))
            except curses.error:
                pass
        else:
            for idx, match in enumerate(self.matches, start=4):
                if idx >= h - 3:
                    try:
                        self.stdscr.addstr(h-2, 4, "More matches below, press any key...", curses.color_pair(3))
                    except curses.error:
                        pass
                    break
                match_str = f"Match {idx-3}: {match['team_a']['name']} ({match['team_a']['odds']}) vs {match['team_b']['name']} ({match['team_b']['odds']})"
                if match.get('draw'):
                    match_str += f" | Draw ({match['draw']['odds']})"
                try:
                    self.stdscr.addstr(idx, 4, match_str, curses.color_pair(4))
                except curses.error:
                    pass
        
        try:
            self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
        except curses.error:
            pass

    def draw_calculate_screen(self):
        h, w = self.stdscr.getmaxyx()
        self.draw_border(h, w)
        title = "❄ Calculate Arbitrage ❄"
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        
        if not self.matches:
            try:
                self.stdscr.addstr(4, 4, "No matches to calculate!", curses.color_pair(2))
                self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
            except curses.error:
                pass
            return
        
        try:
            self.stdscr.addstr(4, 4, f"How many matches to bet on (1-{len(self.matches)})? ", curses.color_pair(3))
        except curses.error:
            pass
        self.stdscr.refresh()
        
        num_matches_str = self.get_user_input(4, 40 + len(str(len(self.matches))), "Number of matches")
        
        try:
            num_matches = int(num_matches_str)
            if num_matches < 1 or num_matches > len(self.matches):
                raise ValueError("Invalid number of matches")
        except ValueError:
            try:
                self.stdscr.addstr(6, 4, f"Please enter a number between 1 and {len(self.matches)}!", curses.color_pair(2))
                self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
            except curses.error:
                pass
            return
        
        selected_matches = self.matches
        if num_matches < len(self.matches):
            selected_matches = []
            self.stdscr.clear()
            self.draw_border(h, w)
            try:
                self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
                self.stdscr.addstr(4, 4, f"Select {num_matches} matches (enter numbers, e.g., '1 2 3'):", curses.color_pair(3))
                for idx, match in enumerate(self.matches, start=1):
                    match_str = f"{idx}: {match['team_a']['name']} vs {match['team_b']['name']}"
                    self.stdscr.addstr(6 + idx, 4, match_str, curses.color_pair(4))
                self.stdscr.addstr(6 + len(self.matches) + 1, 4, "Enter match numbers: ", curses.color_pair(3))
            except curses.error:
                pass
            self.stdscr.refresh()
            
            match_indices = self.get_user_input(6 + len(self.matches) + 1, 24, "Match numbers").split()
            
            try:
                match_indices = [int(i) - 1 for i in match_indices]
                if len(match_indices) != num_matches or any(i < 0 or i >= len(self.matches) for i in match_indices):
                    raise ValueError("Invalid match selection")
                selected_matches = [self.matches[i] for i in match_indices]
            except (ValueError, IndexError):
                try:
                    self.stdscr.addstr(6 + len(self.matches) + 2, 4, "Invalid match selection!", curses.color_pair(2))
                    self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
                except curses.error:
                    pass
                return
        
        self.stdscr.clear()
        self.draw_border(h, w)
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(4, 4, "Selected Matches:", curses.color_pair(3))
            for idx, match in enumerate(selected_matches, start=1):
                match_str = f"Match {idx}: {match['team_a']['name']} vs {match['team_b']['name']}"
                self.stdscr.addstr(6 + idx, 4, match_str, curses.color_pair(4))
            self.stdscr.addstr(6 + len(selected_matches) + 1, 4, "Confirm selection (y/n)? ", curses.color_pair(3))
        except curses.error:
            pass
        self.stdscr.refresh()
        
        confirm = self.get_user_input(6 + len(selected_matches) + 1, 28, "Confirm").lower()
        
        if confirm != 'y':
            try:
                self.stdscr.addstr(6 + len(selected_matches) + 2, 4, "Selection cancelled!", curses.color_pair(2))
                self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
            except curses.error:
                pass
            return
        
        self.stdscr.clear()
        self.draw_border(h, w)
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(4, 4, "Enter total stake amount: ", curses.color_pair(3))
        except curses.error:
            pass
        self.stdscr.refresh()
        
        stake_str = self.get_user_input(4, 28, "Stake amount")
        
        try:
            total_stake = float(stake_str)
            if total_stake <= 0:
                raise ValueError("Stake must be positive")
        except ValueError:
            try:
                self.stdscr.addstr(6, 4, "Invalid stake amount!", curses.color_pair(2))
                self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
            except curses.error:
                pass
            return
        
        self.stdscr.clear()
        self.draw_border(h, w)
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        current_y = 6
        max_bar_width = max(w - 30, 10)
        history_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_stake': total_stake,
            'matches': []
        }
        any_arbitrage = False

        for idx, match in enumerate(selected_matches, start=1):
            if current_y >= h - 3:
                try:
                    self.stdscr.addstr(h-2, 4, "More results below, press any key...", curses.color_pair(3))
                except curses.error:
                    pass
                break
                
            if match.get('draw'):
                odds = [match['team_a']['odds'], match['team_b']['odds'], match['draw']['odds']]
            else:
                odds = [match['team_a']['odds'], match['team_b']['odds']]
            
            result = self.calculate_arbitrage(odds, total_stake)
            
            if result and len(result['stakes']) == len(odds) and len(result['profits']) == len(odds):
                any_arbitrage = True
                match_title = f"Match {idx}: {match['team_a']['name']} vs {match['team_b']['name']}"
                try:
                    self.stdscr.addstr(current_y, 4, match_title, curses.color_pair(4) | curses.A_BOLD)
                except curses.error:
                    pass
                current_y += 1
                
                max_stake = max(result['stakes'])
                max_profit = max(result['profits'])
                
                try:
                    self.stdscr.addstr(current_y, 6, f"Stake on {match['team_a']['name']}: ${result['stakes'][0]:.2f}", curses.color_pair(3))
                    self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(result['stakes'][0], max_stake, max_bar_width), curses.color_pair(1))
                except curses.error:
                    pass
                current_y += 1
                
                try:
                    self.stdscr.addstr(current_y, 6, f"Stake on {match['team_b']['name']}: ${result['stakes'][1]:.2f}", curses.color_pair(3))
                    self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(result['stakes'][1], max_stake, max_bar_width), curses.color_pair(1))
                except curses.error:
                    pass
                current_y += 1
                
                if match.get('draw'):
                    try:
                        self.stdscr.addstr(current_y, 6, f"Stake on Draw: ${result['stakes'][2]:.2f}", curses.color_pair(3))
                        self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(result['stakes'][2], max_stake, max_bar_width), curses.color_pair(1))
                    except curses.error:
                        pass
                    current_y += 1
                
                try:
                    self.stdscr.addstr(current_y, 6, "Stake Distribution:", curses.color_pair(3))
                    current_y += 1
                    pie_chart, percentages = self.draw_ascii_pie(result['stakes'], max_bar_width)
                    self.stdscr.addstr(current_y, 6, pie_chart, curses.color_pair(4))
                    current_y += 1
                    self.stdscr.addstr(current_y, 6, f"[{percentages}]", curses.color_pair(4))
                    current_y += 1
                except curses.error:
                    pass
                
                try:
                    self.stdscr.addstr(current_y, 6, f"Profit if {match['team_a']['name']} wins: ${result['profits'][0]:.2f}", curses.color_pair(3))
                    self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(result['profits'][0], max_profit, max_bar_width), curses.color_pair(4))
                except curses.error:
                    pass
                current_y += 1
                
                try:
                    self.stdscr.addstr(current_y, 6, f"Profit if {match['team_b']['name']} wins: ${result['profits'][1]:.2f}", curses.color_pair(3))
                    self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(result['profits'][1], max_profit, max_bar_width), curses.color_pair(4))
                except curses.error:
                    pass
                current_y += 1
                
                if match.get('draw'):
                    try:
                        self.stdscr.addstr(current_y, 6, f"Profit if Draw: ${result['profits'][2]:.2f}", curses.color_pair(3))
                        self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(result['profits'][2], max_profit, max_bar_width), curses.color_pair(4))
                    except curses.error:
                        pass
                    current_y += 1
                
                try:
                    self.stdscr.addstr(current_y, 6, f"Guaranteed Profit: ${result['guaranteed_profit']:.2f}", curses.color_pair(1) | curses.A_BOLD)
                except curses.error:
                    pass
                current_y += 2

                history_entry['matches'].append({
                    'match': f"{match['team_a']['name']} vs {match['team_b']['name']}",
                    'stakes': result['stakes'],
                    'profits': result['profits'],
                    'guaranteed_profit': result['guaranteed_profit'],
                    'has_draw': match.get('draw') is not None
                })
            else:
                try:
                    self.stdscr.addstr(current_y, 4, f"No arbitrage opportunity for {match['team_a']['name']} vs {match['team_b']['name']}", curses.color_pair(2))
                except curses.error:
                    pass
                current_y += 2
            
            if current_y >= h - 3:
                try:
                    self.stdscr.addstr(h-2, 4, "More results below, press any key...", curses.color_pair(3))
                except curses.error:
                    pass
                break
        
        if any_arbitrage:
            self.history.append(history_entry)
            self.save_history()
        try:
            self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
        except curses.error:
            pass

    def draw_history_screen(self):
        h, w = self.stdscr.getmaxyx()
        self.draw_border(h, w)
        title = "❄ Calculation History ❄"
        try:
            self.stdscr.addstr(1, w//2 - len(title)//2, title, curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass
        
        if not self.history:
            try:
                self.stdscr.addstr(4, 4, "No calculation history yet!", curses.color_pair(2))
                self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
            except curses.error:
                pass
            return
        
        current_y = 4
        max_bar_width = max(w - 30, 10)
        total_stake = sum(entry['total_stake'] for entry in self.history)
        total_profit = sum(sum(match['guaranteed_profit'] for match in entry['matches']) for entry in self.history)
        roi = (total_profit / total_stake * 100) if total_stake > 0 else 0
        
        try:
            self.stdscr.addstr(current_y, 4, f"Summary: Total Stake: ${total_stake:.2f}, Total Profit: ${total_profit:.2f}, ROI: {roi:.1f}%", curses.color_pair(1))
        except curses.error:
            pass
        current_y += 2
        
        for idx, entry in enumerate(self.history, start=1):
            if current_y >= h - 3:
                try:
                    self.stdscr.addstr(h-2, 4, "More history below, press any key...", curses.color_pair(3))
                except curses.error:
                    pass
                break
            try:
                self.stdscr.addstr(current_y, 4, f"Calculation {idx} ({entry['timestamp']}): Stake ${entry['total_stake']:.2f}", curses.color_pair(4))
            except curses.error:
                pass
            current_y += 1
            for match in entry['matches']:
                try:
                    self.stdscr.addstr(current_y, 6, match['match'], curses.color_pair(3))
                except curses.error:
                    pass
                current_y += 1
                max_stake = max(match['stakes'])
                try:
                    self.stdscr.addstr(current_y, 8, f"Stake on Team A: ${match['stakes'][0]:.2f}", curses.color_pair(3))
                    self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(match['stakes'][0], max_stake, max_bar_width), curses.color_pair(1))
                except curses.error:
                    pass
                current_y += 1
                try:
                    self.stdscr.addstr(current_y, 8, f"Stake on Team B: ${match['stakes'][1]:.2f}", curses.color_pair(3))
                    self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(match['stakes'][1], max_stake, max_bar_width), curses.color_pair(1))
                except curses.error:
                    pass
                current_y += 1
                if match['has_draw']:
                    try:
                        self.stdscr.addstr(current_y, 8, f"Stake on Draw: ${match['stakes'][2]:.2f}", curses.color_pair(3))
                        self.stdscr.addstr(current_y, 30, self.draw_ascii_bar(match['stakes'][2], max_stake, max_bar_width), curses.color_pair(1))
                    except curses.error:
                        pass
                    current_y += 1
                try:
                    self.stdscr.addstr(current_y, 8, f"Guaranteed Profit: ${match['guaranteed_profit']:.2f}", curses.color_pair(1))
                except curses.error:
                    pass
                current_y += 2
        
        try:
            self.stdscr.addstr(h-2, 4, "Press any key to return...", curses.color_pair(3))
        except curses.error:
            pass

    def calculate_arbitrage(self, odds_list, total_stake):
        try:
            probabilities = [1/odd for odd in odds_list]
            total_prob = sum(probabilities)
            
            if total_prob >= 1:
                return None
            
            stakes = [(total_stake * p) / total_prob for p in probabilities]
            profits = [(stakes[i] * odds_list[i] - total_stake) for i in range(len(odds_list))]
            
            return {
                'stakes': stakes,
                'profits': profits,
                'guaranteed_profit': (total_stake / total_prob) - total_stake
            }
        except (ZeroDivisionError, ValueError):
            return None

    def clear_matches(self):
        self.stdscr.clear()
        self.draw_border(*self.stdscr.getmaxyx())
        try:
            self.stdscr.addstr(1, self.stdscr.getmaxyx()[1]//2 - 10, "❄ Clear Matches ❄", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(4, 4, "Confirm clear all matches (y/n)? ", curses.color_pair(3))
        except curses.error:
            pass
        self.stdscr.refresh()
        
        confirm = self.get_user_input(4, 36, "Confirm").lower()
        if confirm == 'y':
            self.matches = []
            try:
                self.stdscr.addstr(6, 4, "All matches cleared!", curses.color_pair(1))
            except curses.error:
                pass
        else:
            try:
                self.stdscr.addstr(6, 4, "Clear cancelled!", curses.color_pair(2))
            except curses.error:
                pass
        
        try:
            self.stdscr.addstr(self.stdscr.getmaxyx()[0]-2, 4, "Press any key to return...", curses.color_pair(3))
            self.stdscr.getch()
        except curses.error:
            pass

    def run(self):
        last_size = self.stdscr.getmaxyx()
        while True:
            current_size = self.stdscr.getmaxyx()
            if current_size != last_size:
                self.stdscr.clear()
                self.last_redraw = 0
                last_size = current_size
            
            self.draw_menu()
            
            if self.current_menu == "main":
                self.stdscr.timeout(-1)  # Blocking input for main menu
                try:
                    key = self.stdscr.getch()
                    if key == curses.KEY_UP:
                        self.selected_option = max(0, self.selected_option - 1)
                    elif key == curses.KEY_DOWN:
                        self.selected_option = min(5, self.selected_option + 1)
                    elif key == 10:  # Enter key
                        if self.selected_option == 0:
                            self.add_match()
                        elif self.selected_option == 1:
                            self.current_menu = "view_matches"
                        elif self.selected_option == 2:
                            self.current_menu = "calculate"
                        elif self.selected_option == 3:
                            self.current_menu = "history"
                        elif self.selected_option == 4:
                            self.clear_matches()
                        elif self.selected_option == 5:
                            break
                    elif key in [ord(str(i)) for i in range(1, 7)]:
                        self.selected_option = int(chr(key)) - 1
                        if self.selected_option == 0:
                            self.add_match()
                        elif self.selected_option == 1:
                            self.current_menu = "view_matches"
                        elif self.selected_option == 2:
                            self.current_menu = "calculate"
                        elif self.selected_option == 3:
                            self.current_menu = "history"
                        elif self.selected_option == 4:
                            self.clear_matches()
                        elif self.selected_option == 5:
                            break
                except curses.error:
                    pass
            
            elif self.current_menu in ["view_matches", "calculate", "history"]:
                self.stdscr.timeout(-1)  # Blocking input for these screens
                try:
                    self.stdscr.getch()
                except curses.error:
                    pass
                self.current_menu = "main"

def main(stdscr):
    SureBettingSystem(stdscr)

if __name__ == "__main__":
    wrapper(main)
