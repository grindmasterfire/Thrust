import sys, os, psutil, subprocess, json, datetime, traceback, threading, socket

try:
    from rich.console import Console
    def cprint(msg, style=None): Console().print(msg, style=style)
except ImportError:
    def cprint(msg, style=None): print(msg)

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog

CONFIG_FILE = "cipherworks_config.json"
LOG_FILE = "cipherworks.log"
TELEMETRY_FILE = "cipherworks_telemetry.log"
VERSION = "1.0.0-rc1"
CIRCUIT = "Circuit (mascot 🐾)"

MNEMOS_STATE = {}
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def mnemos_auto(cfg):
    global MNEMOS_STATE
    mfile = cfg.get("mnemos_file", "mnemos.json")
    if os.path.exists(mfile):
        with open(mfile, "r", encoding="utf-8") as f:
            MNEMOS_STATE = json.load(f)
    else:
        MNEMOS_STATE = {}
    # persistent handshake
    MNEMOS_STATE['last_recall'] = datetime.datetime.now().isoformat()
    with open(mfile, "w", encoding="utf-8") as f:
        json.dump(MNEMOS_STATE, f, indent=2)

def mnemos_dump():
    with open("mnemos_export.json", "w", encoding="utf-8") as f:
        json.dump(MNEMOS_STATE, f, indent=2)
    cprint("[bold green]Memory dump exported to mnemos_export.json[/bold green]")

def mnemos_recall():
    global MNEMOS_STATE
    if os.path.exists("mnemos_export.json"):
        with open("mnemos_export.json", "r", encoding="utf-8") as f:
            MNEMOS_STATE = json.load(f)
        cprint("[cyan]Memory restored from export.[/cyan]")

def mnemos_gui(app):
    def dump_cb():
        mnemos_dump()
        messagebox.showinfo("MNEMOS Export", "Memory exported.")
    def recall_cb():
        mnemos_recall()
        messagebox.showinfo("MNEMOS Recall", "Memory recalled from export.")
    mnemos_win = tk.Toplevel(app)
    mnemos_win.title("MNEMOS Kernel Ops")
    tk.Label(mnemos_win, text="MNEMOS memory ops", font=("Segoe UI", 11)).pack(padx=14, pady=8)
    tk.Button(mnemos_win, text="Export Memory", command=dump_cb).pack(padx=8, pady=4)
    tk.Button(mnemos_win, text="Recall Memory", command=recall_cb).pack(padx=8, pady=4)

def run_gui(cfg):
    app = tk.Tk()
    app.title("CipherWorks / THRUST")
    app.geometry("465x340")
    app.configure(bg="#f2f2f7")
    # ... (rest of the GUI code, including CircuitNet, Pro gates, telemetry, etc.)
    # Add MNEMOS tab/button
    tk.Button(app, text="MNEMOS", command=lambda: mnemos_gui(app), bg="#b7e6e6").place(x=12, y=300, width=85)
    # Main loop
    app.mainloop()

def main_cli():
    args = sys.argv[1:]
    cfg = load_config()
    if "--mnemos-dump" in args:
        mnemos_dump()
    elif "--mnemos-recall" in args:
        mnemos_recall()
    elif "--mnemos-export" in args:
        mnemos_dump()
    elif "--mnemos-import" in args:
        mnemos_recall()
    # ... other CLI ops
    else:
        cprint("[yellow]CLI: No command. Use --help for options.[/yellow]")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_cli()
    else:
        cfg = load_config()
        mnemos_auto(cfg)
        run_gui(cfg)
