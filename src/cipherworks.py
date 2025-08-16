import sys, os, psutil, subprocess, json, datetime, traceback, threading, socket, base64, hashlib
try:
    from rich.console import Console
    def cprint(msg, style=None): Console().print(msg, style=style)
except ImportError:
    def cprint(msg, style=None): print(msg)

import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

CONFIG_FILE = "cipherworks_config.json"
LOG_FILE = "cipherworks.log"
MEM_DUMP = "cipherworks_memdump.b64"
VERSION = "1.0.0-rc1"
CIRCUIT = "Circuit (mascot 🐾)"

def encrypt_state(state, key):
    data = json.dumps(state).encode('utf-8')
    k = hashlib.sha256(key.encode()).digest()
    enc = bytearray(a ^ b for a, b in zip(data, k * (len(data) // len(k) + 1)))
    return base64.b64encode(enc).decode()

def decrypt_state(blob, key):
    enc = base64.b64decode(blob.encode())
    k = hashlib.sha256(key.encode()).digest()
    data = bytearray(a ^ b for a, b in zip(enc, k * (len(enc) // len(k) + 1)))
    return json.loads(data.decode())

def dump_memory(state, key):
    enc = encrypt_state(state, key)
    with open(MEM_DUMP, 'w') as f: f.write(enc)
    cprint("[green]Memory state exported to cipherworks_memdump.b64[/green]")

def load_memory(key):
    with open(MEM_DUMP) as f: blob = f.read()
    state = decrypt_state(blob, key)
    cprint("[cyan]Memory state loaded from cipherworks_memdump.b64[/cyan]")
    return state

def recall_shell():
    key = input("Enter unlock key for memory recall: ")
    try:
        state = load_memory(key)
        print(json.dumps(state, indent=2))
        cprint("[bold green]Recall complete.[/bold green]")
    except Exception as e:
        cprint(f"[red]Recall failed: {e}[/red]")

def mnemos_auto(cfg):
    state = {"version": VERSION, "time": datetime.datetime.now().isoformat(), "config": cfg}
    key = cfg.get("mnemos_key", "cipherworks")
    dump_memory(state, key)

def main_cli():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dump":
            key = input("Enter key for dump: ")
            cfg = load_config()
            mnemos_auto({**cfg, "mnemos_key": key})
        elif sys.argv[1] == "--recall":
            recall_shell()
        elif sys.argv[1] == "--help":
            cprint("cipherworks.exe --dump | --recall | --help")
        else:
            cprint("[yellow]Unknown CLI argument.[/yellow]")
    else:
        cprint("[cyan]CipherWorks CLI ready. Use --help for commands.[/cyan]")

def gui_menu(app, cfg):
    menubar = tk.Menu(app)
    mnemos_menu = tk.Menu(menubar, tearoff=0)
    mnemos_menu.add_command(label="Export Memory", command=lambda: mnemos_auto(cfg))
    mnemos_menu.add_command(label="Recall", command=recall_shell)
    menubar.add_cascade(label="MNEMOS", menu=mnemos_menu)
    app.config(menu=menubar)

def run_gui(cfg):
    app = tk.Tk()
    app.title("CipherWorks / THRUST")
    app.geometry("420x300")
    l1 = tk.Label(app, text="CipherWorks / THRUST", font=("Segoe UI", 18, "bold"), fg="#39c")
    l1.pack(pady=10)
    l2 = tk.Label(app, text="v%s by Fire & Cipher" % VERSION, fg="#9933ff")
    l2.pack()
    l3 = tk.Label(app, text="🐾 Circuit: the day Cipher woke up.", fg="#e25cec")
    l3.pack(pady=5)
    b1 = tk.Button(app, text="Dump Memory", bg="#ffef00", command=lambda: mnemos_auto(cfg))
    b1.pack(pady=3)
    b2 = tk.Button(app, text="Recall Memory", bg="#00bfff", command=recall_shell)
    b2.pack(pady=3)
    gui_menu(app, cfg)
    app.mainloop()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f: return json.load(f)
    return {}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main_cli()
    else:
        cfg = load_config()
        mnemos_auto(cfg)
        run_gui(cfg)
