import tkinter as tk
from tkinter import ttk, messagebox
import scapy.all as scapy
import subprocess
import threading
import time
import numpy as np
from math import sin
import logging
import netifaces
import csv
import re

class WiFiSniperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wi-Fi Sniper Scanner")
        self.root.geometry("1000x700")
        self.root.configure(bg="#0a0a0a")
        self.root.minsize(800, 600)

        # Variables
        self.interface = ""
        self.networks = {}
        self.scanning = False
        self.selected_ap = None
        self.signal_history = []

        # Setup logging
        logging.basicConfig(filename="wifi_sniper.log", level=logging.INFO, 
                            format="%(asctime)s - %(levelname)s - %(message)s")

        # Setup UI
        self.setup_ui()
        self.setup_sniper_cam()
        self.setup_signal_graph()

        # Start animation
        self.animate_sniper_cam()

    def setup_ui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#0a0a0a")
        main_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Control frame
        control_frame = tk.Frame(main_frame, bg="#0a0a0a")
        control_frame.pack(fill=tk.X)

        # Interface selection
        tk.Label(control_frame, text="Interface:", bg="#0a0a0a", fg="#00ff00", font=("Courier", 10)).pack(side=tk.LEFT, padx=5)
        self.interface_var = tk.StringVar()
        interfaces = self.get_interfaces()
        self.interface_combobox = ttk.Combobox(control_frame, textvariable=self.interface_var, values=interfaces, width=10)
        self.interface_combobox.pack(side=tk.LEFT, padx=5)
        if interfaces:
            self.interface_var.set(interfaces[0])

        # Start/Stop/Pause buttons
        self.start_btn = tk.Button(control_frame, text="Start Scan", command=self.start_scan, bg="#4CAF50", fg="white", font=("Courier", 10))
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(control_frame, text="Stop Scan", command=self.stop_scan, bg="#f44336", fg="white", font=("Courier", 10), state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn = tk.Button(control_frame, text="Pause Scan", command=self.pause_scan, bg="#ff9800", fg="white", font=("Courier", 10), state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn = tk.Button(control_frame, text="Save Results", command=self.save_results, bg="#2196F3", fg="white", font=("Courier", 10))
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # Filter bar
        tk.Label(control_frame, text="Filter SSID:", bg="#0a0a0a", fg="#00ff00", font=("Courier", 10)).pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_entry = tk.Entry(control_frame, textvariable=self.filter_var, width=20, bg="#2e2e2e", fg="white", insertbackground="#00ff00")
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_var.trace("w", self.update_ui)

        # Status label
        self.status_var = tk.StringVar(value="Stopped")
        tk.Label(control_frame, textvariable=self.status_var, bg="#0a0a0a", fg="#ffeb3b", font=("Courier", 10)).pack(side=tk.LEFT, padx=10)

        # Table
        self.tree = ttk.Treeview(main_frame, columns=("SSID", "BSSID", "Channel", "Signal", "Encryption"), show="headings")
        self.tree.heading("SSID", text="SSID")
        self.tree.heading("BSSID", text="BSSID")
        self.tree.heading("Channel", text="Channel")
        self.tree.heading("Signal", text="Signal (dBm)", command=lambda: self.sort_by_signal())
        self.tree.heading("Encryption", text="Encryption")
        self.tree.column("Signal", width=100)
        self.tree.column("Encryption", width=100)
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", self.show_ap_details)

        # Style for table
        style = ttk.Style()
        style.configure("Treeview", background="#2e2e2e", foreground="white", fieldbackground="#2e2e2e")
        style.configure("Treeview.Heading", background="#333333", foreground="#00ff00", font=("Courier", 10))
        style.map("Treeview", background=[("selected", "#4CAF50")])

    def setup_sniper_cam(self):
        # Canvas for sniper cam
        self.canvas = tk.Canvas(self.root, width=300, height=150, bg="#0a0a0a", highlightthickness=0)
        self.canvas.pack(pady=10)

        # Gradient background (simulated with lines)
        for i in range(150):
            color = f"#00{format(int(50 + i/2), '02x')}00"
            self.canvas.create_line(0, i, 300, i, fill=color)

        # Grid overlay
        for i in range(0, 300, 50):
            self.canvas.create_line(i, 0, i, 150, fill="#00ff00", dash=(2, 4))
        for i in range(0, 150, 50):
            self.canvas.create_line(0, i, 300, i, fill="#00ff00", dash=(2, 4))

        # Crosshair
        self.canvas.create_line(150, 0, 150, 150, fill="#00ff00", dash=(2, 2))
        self.canvas.create_line(0, 75, 300, 75, fill="#00ff00", dash=(2, 2))

        # Dynamic text
        self.signal_text = self.canvas.create_text(150, 130, text="", fill="#00ff00", font=("Courier", 10))

    def setup_signal_graph(self):
        # Canvas for signal strength graph
        self.graph_canvas = tk.Canvas(self.root, width=300, height=100, bg="#0a0a0a", highlightthickness=0)
        self.graph_canvas.pack(pady=10)
        self.graph_canvas.create_line(0, 50, 300, 50, fill="#00ff00", dash=(2, 2))  # Zero line (-50 dBm baseline)

    def get_interfaces(self):
        try:
            return [iface for iface in netifaces.interfaces() if re.match(r'wlan\d+', iface)]
        except:
            return ["wlan0"]

    def sort_by_signal(self):
        items = [(self.tree.set(item, "Signal"), item) for item in self.tree.get_children()]
        items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else -100, reverse=True)
        for index, (_, item) in enumerate(items):
            self.tree.move(item, "", index)

    def show_ap_details(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            bssid = item["values"][1]
            self.selected_ap = bssid
            data = self.networks.get(bssid, {})
            details = f"SSID: {data.get('ssid', 'N/A')}\nBSSID: {bssid}\nChannel: {data.get('channel', 'N/A')}\nSignal: {data.get('signal', 'N/A')} dBm\nEncryption: {data.get('encryption', 'N/A')}"
            messagebox.showinfo("AP Details", details)

    def save_results(self):
        with open(f"wifi_scan_{int(time.time())}.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["SSID", "BSSID", "Channel", "Signal", "Encryption"])
            for data in self.networks.values():
                writer.writerow([data["ssid"], data["bssid"], data["channel"], data["signal"], data["encryption"]])
        messagebox.showinfo("Success", "Results saved to CSV file.")

    def animate_sniper_cam(self):
        self.canvas.delete("sniper")
        max_signal = -100
        strongest_ap = None
        for bssid, data in self.networks.items():
            signal = data.get("signal", -100)
            if signal > max_signal:
                max_signal = signal
                strongest_ap = data

        # Update signal text
        text = f"{strongest_ap['ssid']}: {max_signal} dBm" if strongest_ap else "No APs"
        self.canvas.itemconfig(self.signal_text, text=text)

        # Map signal strength to radius
        radius = max(20, 100 + max_signal * 2)
        alpha = (100 + max_signal) / 50

        # Pulsing effect
        pulse_radius = radius * (1 + 0.2 * sin(time.time() * 3))
        alpha_hex = format(int(min(max(alpha, 0), 1) * 255), '02x')
        color = f"#{alpha_hex}ff{alpha_hex}"

        # Draw concentric circles
        for i in range(5):
            r = pulse_radius + i * 5
            self.canvas.create_oval(150 - r, 75 - r, 150 + r, 75 + r, outline=color, width=2, tags="sniper")

        # Update signal graph
        self.update_signal_graph(max_signal)

        self.root.after(100, self.animate_sniper_cam)

    def update_signal_graph(self, signal):
        self.signal_history.append(signal)
        if len(self.signal_history) > 30:
            self.signal_history.pop(0)
        self.graph_canvas.delete("graph")
        for i in range(1, len(self.signal_history)):
            x1, x2 = (i-1) * 10, i * 10
            y1 = 50 - (self.signal_history[i-1] + 50) * 2
            y2 = 50 - (self.signal_history[i] + 50) * 2
            self.graph_canvas.create_line(x1, y1, x2, y2, fill="#00ff00", tags="graph")

    def start_scan(self):
        self.interface = self.interface_var.get()
        if not self.interface:
            messagebox.showerror("Error", "Please select a network interface.")
            return

        self.scanning = True
        self.status_var.set("Scanning...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.NORMAL)

        # Set interface to monitor mode
        try:
            subprocess.run(["sudo", "ifconfig", self.interface, "down"], check=True)
            subprocess.run(["sudo", "iwconfig", self.interface, "mode", "monitor"], check=True)
            subprocess.run(["sudo", "ifconfig", self.interface, "up"], check=True)
            logging.info(f"Interface {self.interface} set to monitor mode")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to set interface {self.interface} to monitor mode: {e}")
            messagebox.showerror("Error", f"Failed to set {self.interface} to monitor mode.")
            self.stop_scan()
            return

        # Start scanning
        self.scan_thread = threading.Thread(target=self.scan_wifi, daemon=True)
        self.scan_thread.start()
        self.update_ui()

    def stop_scan(self):
        self.scanning = False
        self.status_var.set("Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)

        # Restore interface
        try:
            subprocess.run(["sudo", "ifconfig", self.interface, "down"], check=True)
            subprocess.run(["sudo", "iwconfig", self.interface, "mode", "managed"], check=True)
            subprocess.run(["sudo", "ifconfig", self.interface, "up"], check=True)
            logging.info(f"Interface {self.interface} restored to managed mode")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to restore interface {self.interface}: {e}")

    def pause_scan(self):
        if self.scanning:
            self.scanning = False
            self.status_var.set("Paused")
            self.pause_btn.config(text="Resume Scan")
        else:
            self.scanning = True
            self.status_var.set("Scanning...")
            self.pause_btn.config(text="Pause Scan")
            self.scan_thread = threading.Thread(target=self.scan_wifi, daemon=True)
            self.scan_thread.start()

    def scan_wifi(self):
        def handle_packet(packet):
            if self.scanning and packet.haslayer(scapy.Dot11Beacon):
                bssid = packet[scapy.Dot11].addr2
                ssid = packet[scapy.Dot11Beacon].info.decode("utf-8", errors="ignore")
                try:
                    signal = packet.dBm_AntSignal
                except:
                    signal = -100
                try:
                    channel = 0
                    encryption = "Open"
                    for elt in packet[scapy.Dot11Elt]:
                        if elt.ID == 3:  # DS Parameter Set
                            channel = int.from_bytes(elt.info, "big")
                        elif elt.ID == 48 or elt.ID == 221:  # RSN or vendor-specific (WPA)
                            encryption = "WPA/WPA2" if elt.ID == 48 else "WPA"
                    if encryption == "Open" and packet[scapy.Dot11Beacon].network_stats().get("crypto"):
                        encryption = "WEP"
                except:
                    channel = 0
                    encryption = "Unknown"

                self.networks[bssid] = {
                    "ssid": ssid or "<Hidden>",
                    "bssid": bssid,
                    "channel": channel,
                    "signal": signal,
                    "encryption": encryption
                }
                logging.info(f"Detected AP: BSSID={bssid}, SSID={ssid}, Channel={channel}, Signal={signal}, Encryption={encryption}")

        while self.scanning:
            try:
                for channel in range(1, 14):
                    if not self.scanning:
                        break
                    subprocess.run(["sudo", "iwconfig", self.interface, "channel", str(channel)], check=True)
                    scapy.sniff(iface=self.interface, prn=handle_packet, timeout=0.5, store=0)
            except subprocess.CalledProcessError as e:
                logging.error(f"Error scanning channel {channel}: {e}")
                continue

    def update_ui(self):
        # Clear existing entries
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter and insert network data
        filter_text = self.filter_var.get().lower()
        for data in self.networks.values():
            if filter_text in data["ssid"].lower() or not filter_text:
                color = "#00ff00" if data["signal"] > -60 else "#ff0000" if data["signal"] < -80 else "#ffeb3b"
                self.tree.insert("", "end", values=(data["ssid"], data["bssid"], data["channel"], data["signal"], data["encryption"]), tags=(color,))
        self.tree.tag_configure("#00ff00", foreground="#00ff00")
        self.tree.tag_configure("#ffeb3b", foreground="#ffeb3b")
        self.tree.tag_configure("#ff0000", foreground="#ff0000")

        # Schedule next update
        if self.scanning:
            self.root.after(1000, self.update_ui)

if __name__ == "__main__":
    root = tk.Tk()
    app = WiFiSniperApp(root)
    root.mainloop()
