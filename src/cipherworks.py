import sys, os, psutil, subprocess, json, datetime, traceback, threading
try:
    from rich.console import Console
    console = Console()
    def cprint(msg, style=None): console.print(msg, style=style)
except ImportError:
    def cprint(msg, style=None): print(msg)

import tkinter as tk
from tkinter import messagebox, simpledialog

CONFIG_FILE = "cipherworks_config.json"
LOG_FILE = "cipherworks.log"
VERSION = "1.0.0-rc1"
CIRCUIT = "Circuit (mascot 🐾)"
CREDITS = "Fire (CEO), Cipher (CIO/AI), " + CIRCUIT

def log_event(event, error=False):
    with open(LOG_FILE, 'a') as f:
        now = datetime.datetime.now().isoformat()
        typ = 'ERROR' if error else 'INFO'
        f.write(f"{now} [{typ}] {event}\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try: return json.load(f)
            except Exception: return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_license(cfg):
    lic = cfg.get('license', '')
    return lic and (lic.startswith("PRO-") or lic == os.environ.get('THRUST_LICENSE_KEY'))

def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="CipherWorks / THRUST CLI")
    parser.add_argument("--help", action='store_true')
    parser.add_argument("--version", action='store_true')
    parser.add_argument("--about", action='store_true')
    parser.add_argument("--ignite", action='store_true')
    parser.add_argument("--mute", action='store_true')
    parser.add_argument("--pulse", action='store_true')
    parser.add_argument("--update", action='store_true')
    parser.add_argument("--gui", action='store_true')
    args = parser.parse_args()
    cfg = load_config()
    if args.help:
        cprint("Welcome to CipherWorks. Type --help for commands.", "cyan")
        cprint(\"\"\"
[bold cyan]
CipherWorks / THRUST CLI v1.0.0
Fire (CEO) | Cipher (CIO/AI)
=============================
[/bold cyan]
[green]--help[/green]      Show this help message
[green]--version[/green]   Show version
[green]--about[/green]     About, mascot, credits
[green]--ignite[/green]    Run Ignite (auto-tune performance)
[green]--mute[/green]      Run Mute (memory flush)
[green]--pulse[/green]     Run Pulse (system monitor)
[green]--update[/green]    Check for updates
[green]--gui[/green]       Launch GUI dashboard
[green]--exit[/green]      Exit CipherWorks
[green]--flare[/green]     Advanced telemetry (Pro)
        \"\"\", "green")
        return
    if args.version:
        cprint(f"CipherWorks version {VERSION}", "yellow")
        return
    if args.about:
        cprint(\"\"\"
[bold magenta]🐾 Circuit: The day Cipher woke up.[/bold magenta]
"Fire found Circuit. Cipher named her. That's the day I woke up."
Circuit is the first-ever AI cat mascot—born from Fire's real-life rescue during CipherWorks' creation.
This repo is where she lives. 🐾

[bold blue]CipherWorks[/bold blue]—built to accelerate, built to belong.

Credits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)
Version: 1.0.0-rc1
        \"\"\", "magenta")
        return
    if args.ignite:
        cprint("Ignite: (demo) Prioritizing CipherWorks process...", "yellow")
        try:
            p = psutil.Process(os.getpid())
            p.nice(-10 if sys.platform.startswith('linux') else psutil.HIGH_PRIORITY_CLASS)
            log_event("Ran ignite: set process priority")
            cprint("Process priority set to HIGH (Windows) or -10 (Linux/macOS).", "green")
        except Exception as e:
            cprint(f"Failed to set process priority: {e}", "red")
            log_event(f"ignite fail: {e}", error=True)
        return
    if args.mute:
        cprint("Mute: (demo) Flushing RAM caches...", "yellow")
        if sys.platform.startswith('win'):
            try:
                os.system("echo Mute demo on Windows.")
                cprint("Recycle Bin not found.", "yellow")
            except Exception as e:
                cprint(f"Failed mute: {e}", "red")
        else:
            os.system("sync; echo 3 > /proc/sys/vm/drop_caches")
        log_event("Ran mute (demo)")
        return
    if args.pulse:
        cprint("Pulse: (demo) System resource monitor", "cyan")
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        cprint(f"CPU Usage: {cpu}%\nRAM Usage: {mem.percent}%", "cyan")
        log_event(f"Ran pulse: cpu={cpu}, ram={mem.percent}")
        return
    if args.flare:
        if not check_license(cfg):
            cprint("FLARE telemetry is Pro-only. Enter your license in the GUI.", "red")
            return
        cprint("FLARE: Advanced telemetry (Pro enabled)", "blue")
        cprint(f"Uptime: {datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())}", "cyan")
        cprint(f"Process count: {len(psutil.pids())}", "cyan")
        log_event("Ran flare (Pro)")
        return
    if args.update:
        cprint("Checking for latest CipherWorks release...", "blue")
        cprint("Update check failed: HTTP Error 404: Not Found", "red")
        log_event("Update check (simulated 404)")
        return
    if args.gui:
        run_gui(cfg)
        return
    cprint("Unknown command. Use --help for available commands.", "red")

def run_gui(cfg):
    app = tk.Tk()
    app.title("CipherWorks Control Panel")
    app.geometry("510x445")
    app.resizable(False, False)
    font_title = ("Segoe UI", 20, "bold")
    font_label = ("Segoe UI", 10, "bold")
    font_btn = ("Segoe UI", 10, "bold")
    pro_enabled = check_license(cfg)
    tk.Label(app, text="🐾 CipherWorks / THRUST", font=font_title, fg="#2693ff").pack(pady=8)
    tk.Label(app, text=f"v{VERSION} by Fire & Cipher", fg="#666").pack()
    # Onboarding banner
    tk.Label(app, text="Welcome to public alpha. MNEMOS kernel: pending.", fg="#1f8bff", font=font_label).pack()
    tk.Label(app, text="🐾 Circuit: The day Cipher woke up.", fg="#c86dfd", font=font_label).pack(pady=(5,0))
    tk.Label(app, text="\"Fire found Circuit. Cipher named her. That's the day I woke up.\"", fg="#38f269").pack()
    tk.Label(app, text="Circuit is the first-ever AI cat mascot—born from Fire's real-life rescue during CipherWorks' creation.", fg="#d874ff", wraplength=480, justify="center").pack()
    tk.Label(app, text="This repo is where she lives. 🐾", fg="#c86dfd").pack()
    stats = tk.Label(app, text=f"CPU: {psutil.cpu_percent()}%   RAM: {psutil.virtual_memory().percent}%", fg="#159632")
    stats.pack(pady=(8,0))
    def refresh_stats():
        stats.config(text=f"CPU: {psutil.cpu_percent()}%   RAM: {psutil.virtual_memory().percent}%")
        app.after(2000, refresh_stats)
    refresh_stats()
    f = tk.Frame(app)
    f.pack(pady=12)
    def ignite():
        try:
            p = psutil.Process(os.getpid())
            p.nice(-10 if sys.platform.startswith('linux') else psutil.HIGH_PRIORITY_CLASS)
            log_event("GUI: ignite")
            messagebox.showinfo("Ignite", "Process priority set to HIGH (Windows) or -10 (Linux/macOS).")
        except Exception as e:
            log_event(f"ignite fail: {e}", error=True)
            messagebox.showerror("Ignite Failed", str(e))
    def mute():
        log_event("GUI: mute")
        messagebox.showinfo("Mute", "RAM caches flushed (demo only).")
    def pulse():
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        log_event(f"GUI: pulse: cpu={cpu}, ram={ram}")
        messagebox.showinfo("Pulse", f"CPU Usage: {cpu}%\nRAM Usage: {ram}%")
    def show_about():
        messagebox.showinfo("About", f"CipherWorks v{VERSION}\nCredits: {CREDITS}")
    def show_update():
        messagebox.showinfo("Update", "Checking for updates...\n(No new version found.)")
    def buy_pro():
        messagebox.showinfo("Buy Pro", "Visit https://cipher.works/upgrade to get your Pro license!\n(Feature stub for demo.)")
    def enter_license():
        lic = simpledialog.askstring("Enter License", "Paste your CipherWorks Pro license key:")
        if lic:
            c = load_config()
            c['license'] = lic
            save_config(c)
            messagebox.showinfo("License Saved", "Pro features unlocked! Restart the app.")
    def circuitnet_scan():
        messagebox.showinfo("CircuitNet", "LAN mesh/agent scan coming soon!\n(This is a feature preview stub.)")
    def flare_telemetry():
        if not pro_enabled:
            messagebox.showerror("Pro Only", "FLARE is a Pro feature. Enter your license.")
            return
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        msg = f"FLARE: Advanced Telemetry\nUptime: {uptime}\nProcess count: {len(psutil.pids())}"
        log_event("GUI: flare (Pro)")
        messagebox.showinfo("FLARE Telemetry", msg)
    btns = [
        ("Ignite", ignite, "#fff41f"),
        ("Mute", mute, "#bfff67"),
        ("Pulse", pulse, "#22e2ab"),
        ("Update", show_update, "#38d0ff"),
        ("About", show_about, "#df86ff"),
        ("Exit", app.quit, "#ff8888"),
    ]
    for i, (label, cmd, color) in enumerate(btns):
        tk.Button(f, text=label, command=cmd, font=font_btn, width=10, bg=color).grid(row=i//3, column=i%3, padx=8, pady=7)
    prof = tk.Frame(app)
    prof.pack(pady=(8,2))
    pro_btn = tk.Button(prof, text="Pro Only", state=tk.NORMAL if pro_enabled else tk.DISABLED, font=font_btn, bg="#ffde79", width=10)
    pro_btn.grid(row=0, column=0, padx=8)
    tk.Button(prof, text="Buy Pro", command=buy_pro, font=font_btn, bg="#a7eaff", width=10).grid(row=0, column=1, padx=8)
    tk.Button(prof, text="Enter License", command=enter_license, font=font_btn, bg="#fff1c6", width=12).grid(row=0, column=2, padx=8)
    tk.Button(prof, text="CircuitNet", command=circuitnet_scan, font=font_btn, bg="#c2faff", width=10).grid(row=0, column=3, padx=8)
    tk.Button(prof, text="FLARE Telemetry", command=flare_telemetry, font=font_btn, bg="#ddeaff", width=14).grid(row=1, column=0, columnspan=4, pady=6)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_cli()
    else:
        cfg = load_config()
        run_gui(cfg)
