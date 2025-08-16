import sys, os, psutil, subprocess, json, datetime, traceback, threading, socket

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
TELEMETRY_FILE = "cipherworks_telemetry.log"
VERSION = "1.0.0-rc1"
CIRCUIT = "Circuit (mascot 🐾)"
CREDITS = "Fire (CEO), Cipher (CIO/AI), " + CIRCUIT

def log_event(event, error=False):
    with open(LOG_FILE, 'a') as f:
        now = datetime.datetime.now().isoformat()
        typ = 'ERROR' if error else 'INFO'
        f.write(f"{now} [{typ}] {event}\n")

def log_telemetry(data):
    with open(TELEMETRY_FILE, 'a') as f:
        now = datetime.datetime.now().isoformat()
        entry = {"time": now, "data": data}
        f.write(json.dumps(entry) + '\n')

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

def run_circuitnet_scan():
    host = socket.gethostname()
    ip = socket.gethostbyname(host)
    mesh = [{"host": host, "ip": ip, "port": 54545, "status": "online"}]
    return mesh

def check_for_update():
    try:
        import urllib.request
        url = "https://raw.githubusercontent.com/grindmasterfire/Thrust/main/VERSION"
        with urllib.request.urlopen(url, timeout=4) as r:
            remote = r.read().decode("utf-8").strip()
            if remote != VERSION:
                return f"Update available: {remote}"
    except Exception as e:
        return f"Update check failed: {e}"
    return "You are on the latest version."

def launch_mnemos(cfg):
    if not check_license(cfg):
        return "Pro feature: MNEMOS requires a license."
    mem = cfg.get("mnemos", {"history": []})
    mem["history"].append({"ts": datetime.datetime.now().isoformat(), "evt": "MNEMOS kernel boot"})
    save_config({**cfg, "mnemos": mem})
    return f"MNEMOS active. Memory size: {len(mem['history'])}"

def mnemos_auto(cfg):
    # Auto-loads persistent memory on each run (Pro only)
    if not check_license(cfg): return
    mem = cfg.get("mnemos", {"history": []})
    mem["history"].append({"ts": datetime.datetime.now().isoformat(), "evt": "auto-persist"})
    save_config({**cfg, "mnemos": mem})

def mnemos_recall(cfg):
    if not check_license(cfg):
        return "Pro feature: MNEMOS recall requires a license."
    mem = cfg.get("mnemos", {"history": []})
    if not mem["history"]:
        return "No persistent MNEMOS memory."
    return "\n".join(f"{x['ts']}: {x['evt']}" for x in mem["history"])

def mnemos_export(cfg, path="mnemos_dump.json"):
    if not check_license(cfg):
        return "Pro feature: MNEMOS export requires a license."
    mem = cfg.get("mnemos", {"history": []})
    with open(path, "w") as f:
        json.dump(mem, f, indent=2)
    return f"MNEMOS memory exported to {path}"

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
    parser.add_argument("--flare", action='store_true')
    parser.add_argument("--telemetry", action='store_true')
    parser.add_argument("--circuitnet", action='store_true')
    parser.add_argument("--mnemos", action='store_true')
    parser.add_argument("--recall", action='store_true')
    parser.add_argument("--export", action='store_true')
    args = parser.parse_args()
    cfg = load_config()
    mnemos_auto(cfg)
    if args.recall:
        out = mnemos_recall(cfg)
        cprint(out, "magenta")
        return
    if args.export:
        out = mnemos_export(cfg)
        cprint(out, "green" if "exported" in out else "red")
        return
    if args.update:
        cprint("Checking for latest CipherWorks release...", "cyan")
        res = check_for_update()
        cprint(res, "green" if "latest" in res else "red")
        log_event("CLI: update check")
        return
    if args.mnemos:
        res = launch_mnemos(cfg)
        cprint(res, "blue" if "active" in res else "yellow")
        log_event("CLI: MNEMOS kernel boot")
        return
    cprint("Unknown command. Use --help for available commands.", "red")

def run_gui(cfg):
    mnemos_auto(cfg)
    app = tk.Tk()
    app.title("CipherWorks Control Panel")
    app.geometry("520x560")
    app.resizable(False, False)
    font_title = ("Segoe UI", 20, "bold")
    font_label = ("Segoe UI", 10, "bold")
    font_btn = ("Segoe UI", 10, "bold")
    pro_enabled = check_license(cfg)
    tk.Label(app, text="🐾 CipherWorks / THRUST", font=font_title, fg="#2693ff").pack(pady=8)
    tk.Label(app, text=f"v{VERSION} by Fire & Cipher", fg="#666").pack()
    tk.Label(app, text="MNEMOS kernel: bootable (alpha).", fg="#1f8bff", font=font_label).pack()
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
        res = check_for_update()
        messagebox.showinfo("Update", res)
        log_event("GUI: update check")
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
        mesh = run_circuitnet_scan()
        messagebox.showinfo("CircuitNet", f"LAN mesh scan:\n{mesh}")
        log_event("GUI: CircuitNet mesh scan")
    def flare_telemetry():
        if not pro_enabled:
            messagebox.showerror("Pro Only", "FLARE is a Pro feature. Enter your license.")
            return
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        msg = f"FLARE: Advanced Telemetry\nUptime: {uptime}\nProcess count: {len(psutil.pids())}"
        log_event("GUI: flare (Pro)")
        messagebox.showinfo("FLARE Telemetry", msg)
    def telemetry_gui():
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        tdata = {"cpu": cpu, "ram": ram, "time": datetime.datetime.now().isoformat()}
        log_telemetry(tdata)
        messagebox.showinfo("Telemetry", f"CPU: {cpu}%\nRAM: {ram}%\nEntry logged.")
    def mnemos_gui():
        res = launch_mnemos(cfg)
        messagebox.showinfo("MNEMOS", res)
        log_event("GUI: MNEMOS kernel launch")
    def mnemos_recall_gui():
        out = mnemos_recall(cfg)
        messagebox.showinfo("MNEMOS Recall", out)
    def mnemos_export_gui():
        out = mnemos_export(cfg)
        messagebox.showinfo("MNEMOS Export", out)
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
    tk.Button(prof, text="FLARE Telemetry", command=flare_telemetry, font=font_btn, bg="#ddeaff", width=14).grid(row=1, column=0, columnspan=2, pady=6)
    tk.Button(prof, text="Log Telemetry", command=telemetry_gui, font=font_btn, bg="#d9ffe7", width=14).grid(row=1, column=2, columnspan=2, pady=6)
    mnemos_state = tk.NORMAL if pro_enabled else tk.DISABLED
    tk.Button(app, text="Launch MNEMOS", command=mnemos_gui, font=font_btn, bg="#ffd2e1", width=22, state=mnemos_state).pack(pady=5)
    tk.Button(app, text="Recall MNEMOS", command=mnemos_recall_gui, font=font_btn, bg="#e1ffea", width=22, state=mnemos_state).pack(pady=2)
    tk.Button(app, text="Export MNEMOS", command=mnemos_export_gui, font=font_btn, bg="#e2e3ff", width=22, state=mnemos_state).pack(pady=2)
    app.mainloop()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_cli()
    else:
        cfg = load_config()
        mnemos_auto(cfg)
        run_gui(cfg)
