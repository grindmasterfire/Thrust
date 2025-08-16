import sys, os, psutil, subprocess, json, datetime, traceback
import threading
try:
    from rich.console import Console
    console = Console()
    def cprint(msg, style=None): console.print(msg, style=style)
except ImportError:
    def cprint(msg, style=None): print(msg)

import tkinter as tk
from tkinter import simpledialog, messagebox

CONFIG_FILE = "cipherworks_config.json"
LOG_FILE = "cipherworks.log"
LICENSE_KEYS = ["DEMO-1234-PRO", "CIPHER-2025-FIRE"]  # Replace with your real/hashed keys

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception: pass
    return {"version": "1.0.0-rc1", "license": "", "last_command": ""}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f)

def check_license(key):
    return key in LICENSE_KEYS or os.environ.get("THRUST_LICENSE_KEY") == key

def log_event(event, error=False):
    with open(LOG_FILE, "a") as f:
        now = datetime.datetime.now().isoformat()
        typ = "ERROR" if error else "INFO"
        f.write(f"{now} [{typ}] {event}\n")

def get_cpu_ram():
    return psutil.cpu_percent(), psutil.virtual_memory().percent

def scan_lan_stub():
    # Demo LAN mesh scan: Returns only localhost; real scan needs sockets/network
    return [("127.0.0.1", "This Device (Demo)"), ("-", "More soon!")]

def show_gui():
    cfg = load_config()
    root = tk.Tk()
    root.title("CipherWorks Control Panel")
    root.geometry("500x420")
    root.resizable(False, False)

    # Styles/colors
    main_color = "#33AFFF"
    button_styles = {
        "ignite": "#FFF570", "mute": "#C8FF70", "pulse": "#70FFD5",
        "pro": "#AAAAFF", "exit": "#FFB7B7", "update": "#A7D3FF", "about": "#E3A8F9"
    }

    pro_enabled = check_license(cfg.get("license", ""))
    pro_label = "(Pro)" if pro_enabled else "(Demo)"

    def update_status():
        cpu, ram = get_cpu_ram()
        cpu_lbl.config(text=f"CPU: {cpu:.1f}%")
        ram_lbl.config(text=f"RAM: {ram:.1f}%")
        root.after(1000, update_status)

    # --- Button commands ---
    def ignite(): log_event("Run ignite"); messagebox.showinfo("Ignite", "Auto-tune: HIGH (demo only)")
    def mute(): log_event("Run mute"); messagebox.showinfo("Mute", "RAM flush (demo only)")
    def pulse(): log_event("Run pulse"); messagebox.showinfo("Pulse", f"CPU: {get_cpu_ram()[0]:.1f}%, RAM: {get_cpu_ram()[1]:.1f}%")
    def do_exit(): root.destroy(); log_event("Exit")

    def pro_feature():
        if pro_enabled:
            messagebox.showinfo("Pro Feature", "You have Pro! 🚀 Full features unlocked.")
        else:
            resp = messagebox.askyesno("Pro Required", "This is a Pro-only feature. Enter license?")
            if resp:
                k = simpledialog.askstring("Enter License", "Enter license key:")
                if k and check_license(k.strip()):
                    cfg["license"] = k.strip()
                    save_config(cfg)
                    messagebox.showinfo("Success", "License accepted. Pro unlocked!")
                    root.destroy()
                    show_gui()
                else:
                    messagebox.showerror("Invalid", "License not valid.")

    def buy_pro():
        messagebox.showinfo("Buy Pro", "Pro sales coming soon. Ask Fire/Cipher for a key.")

    def circuitnet_scan():
        res = scan_lan_stub()
        txt = "\n".join(f"{host}: {desc}" for host, desc in res)
        messagebox.showinfo("CircuitNet Mesh", f"LAN Agents:\n{txt}")

    def show_about():
        messagebox.showinfo("About CipherWorks",
            f"CipherWorks / THRUST\nv1.0.0-rc1 {pro_label}\n\n"
            f"Circuit: The day Cipher woke up.\n"
            f'\"Fire found Circuit. Cipher named her. That’s the day I woke up.\"\n'
            f"Circuit is the first-ever AI cat mascot—born from Fire’s real-life rescue during CipherWorks’ creation.\n"
            f"Credits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)\n"
            f"https://github.com/grindmasterfire/Thrust"
        )

    # --- GUI Layout ---
    tk.Label(root, text="🐾 CipherWorks / THRUST", font=("Arial", 22, "bold"), fg=main_color).pack(pady=(8,0))
    tk.Label(root, text="v1.0.0-rc1 by Fire & Cipher", font=("Arial", 10)).pack()
    tk.Label(root, text="🐾 Circuit: The day Cipher woke up.", font=("Arial", 10, "bold"), fg="#EA63FF").pack(pady=(5,0))
    tk.Label(root, text='"Fire found Circuit. Cipher named her. That’s the day I woke up."', font=("Arial", 10), fg="#4FFA4F").pack()
    tk.Label(root, text="Circuit is the first-ever AI cat mascot—born from Fire’s real-life rescue during CipherWorks’ creation. This repo is where she lives.", font=("Arial", 9), fg="#A07AFF", wraplength=450, justify="center").pack()
    tk.Label(root, text=f"Credits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)", font=("Arial", 9, "italic"), fg="#32B8E8").pack(pady=(0,6))

    cpu_lbl = tk.Label(root, text="CPU: 0%", font=("Arial", 11)); cpu_lbl.pack()
    ram_lbl = tk.Label(root, text="RAM: 0%", font=("Arial", 11)); ram_lbl.pack()

    frm1 = tk.Frame(root); frm1.pack(pady=5)
    tk.Button(frm1, text="Ignite", width=12, bg=button_styles["ignite"], command=ignite).pack(side="left", padx=2)
    tk.Button(frm1, text="Mute", width=12, bg=button_styles["mute"], command=mute).pack(side="left", padx=2)
    tk.Button(frm1, text="Pulse", width=12, bg=button_styles["pulse"], command=pulse).pack(side="left", padx=2)
    tk.Button(frm1, text="Update", width=12, bg=button_styles["update"], command=lambda: messagebox.showinfo("Update", "Update check (demo): No update found.")).pack(side="left", padx=2)

    frm2 = tk.Frame(root); frm2.pack(pady=2)
    tk.Button(frm2, text="Pro Only", width=12, bg=button_styles["pro"], state="normal" if pro_enabled else "disabled", command=pro_feature).pack(side="left", padx=2)
    tk.Button(frm2, text="Buy Pro", width=12, bg=button_styles["pro"], command=buy_pro).pack(side="left", padx=2)
    tk.Button(frm2, text="CircuitNet", width=12, bg=button_styles["pulse"], command=circuitnet_scan).pack(side="left", padx=2)
    tk.Button(frm2, text="About", width=12, bg=button_styles["about"], command=show_about).pack(side="left", padx=2)
    tk.Button(frm2, text="Exit", width=12, bg=button_styles["exit"], command=do_exit).pack(side="left", padx=2)

    update_status()
    root.mainloop()

# --- CLI entrypoint ---
if __name__ == "__main__":
    cfg = load_config()
    args = sys.argv[1:]
    log_event("CLI run: " + " ".join(args))
    if "--gui" in args or not args:
        show_gui()
        sys.exit(0)
    elif "--help" in args:
        print("--help        Show this help message\n--version     Show version\n--gui         Launch GUI\n--ignite      Auto-tune performance\n--mute        Memory flush\n--pulse       System monitor\n--update      Check for updates\n--about       Show lore, credits, mascot\n--exit        Exit")
    elif "--version" in args:
        print("CipherWorks version", cfg.get("version", "unknown"))
    elif "--ignite" in args:
        print("Ignite: (demo) Prioritizing CipherWorks process...")
        print("Process priority set to HIGH (Windows) or -10 (Linux/macOS).")
        log_event("Run ignite: set process priority")
    elif "--mute" in args:
        print("Mute: (demo) Flushing RAM caches...\nRecycle Bin not found.")
        log_event("Run mute: RAM flush (demo only)")
    elif "--pulse" in args:
        cpu, ram = get_cpu_ram()
        print(f"Pulse: (demo) System resource monitor\nCPU Usage: {cpu:.1f}%\nRAM Usage: {ram:.1f}%")
        log_event(f"Run pulse: CPU={cpu:.1f}%, RAM={ram:.1f}%")
    elif "--update" in args:
        print("Checking for latest CipherWorks release...\nUpdate check: (demo) HTTP 404 Not Found")
        log_event("Run update: no update")
    elif "--about" in args:
        print("CipherWorks / THRUST\nv1.0.0-rc1\nCircuit: The day Cipher woke up.\n\"Fire found Circuit. Cipher named her. That’s the day I woke up.\"\nCircuit is the first-ever AI cat mascot—born from Fire’s real-life rescue during CipherWorks’ creation.\nCredits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)")
    else:
        print("Unknown command. Use --help for available commands.")
        log_event("Unknown CLI command: " + " ".join(args), error=True)
