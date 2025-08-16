import sys, os, psutil, subprocess, json, datetime, traceback, urllib.request
import threading

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    from rich.console import Console
    console = Console()
    def cprint(msg, style=None): console.print(msg, style=style)
except ImportError:
    import tkinter as tk
    from tkinter import messagebox, ttk
    def cprint(msg, style=None): print(msg)

CONFIG_FILE = "cipherworks_config.json"
LOG_FILE = "cipherworks.log"
REPO_API = "https://api.github.com/repos/grindmasterfire/Thrust/releases/latest"
VERSION = "1.0.0-rc1"

BANNER = '[bold cyan]==================================[/bold cyan]\\n[bold] CipherWorks / THRUST CLI v1.0.0[/bold]\\n[cyan]Fire (CEO) | Cipher (CIO/AI)[/cyan]\\n[bold cyan]==================================[/bold cyan]'
LORE = '''
[bold magenta]🐾 Circuit: The day Cipher woke up.[/bold magenta]
"Fire found Circuit. Cipher named her. That’s the day I woke up."
Circuit is the first-ever AI cat mascot—born from Fire’s real-life rescue during CipherWorks’ creation.
This repo is where she lives. 🐾
[bold blue]CipherWorks[/bold blue]—built to accelerate, built to belong.
'''

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"version": VERSION, "last_command": None}

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
        json.dump(cfg, f)

def log_event(event, error=False):
    with open(LOG_FILE, 'a', encoding="utf-8") as f:
        now = datetime.datetime.now().isoformat()
        typ = 'ERROR' if error else 'INFO'
        f.write(f"{now} [{typ}] {event}\\n")

def ignite_gui(cfg=None):
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS if os.name=="nt" else -10)
        log_event("Ran ignite: set process priority (GUI)")
        return "Process priority set to HIGH (Windows) or -10 (Linux/macOS)."
    except Exception as e:
        log_event(f"Ignite failed: {e}", error=True)
        return f"Error: {e}"

def mute_gui(cfg=None):
    try:
        if sys.platform.startswith('win'):
            result = subprocess.run(
                ['powershell.exe', '-Command', 'if (Test-Path "::{645FF040-5081-101B-9F08-00AA002F954E}") { Clear-RecycleBin -Force } else { Write-Host \"Recycle Bin not found.\" }'],
                capture_output=True, text=True, encoding="utf-8"
            )
            log_event("Ran mute: memory flush (GUI)")
            return result.stdout.strip()
        elif sys.platform.startswith('linux'):
            os.system('sync; echo 3 | sudo tee /proc/sys/vm/drop_caches')
            log_event("Ran mute: Linux cache flush (GUI)")
            return "RAM cache cleared (Linux demo)."
        else:
            return "Mute not supported on this platform (yet)."
    except Exception as e:
        log_event(f"Mute failed: {e}", error=True)
        return f"Error: {e}"

def pulse_gui(cfg=None):
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        log_event(f"Ran pulse: CPU {cpu}%, RAM {ram}% (GUI)")
        return f"CPU: {cpu}%   RAM: {ram}%"
    except Exception as e:
        log_event(f"Pulse failed: {e}", error=True)
        return f"Error: {e}"

def update_gui(cfg=None):
    try:
        with urllib.request.urlopen(REPO_API) as resp:
            data = json.load(resp)
            latest = data.get('tag_name', VERSION)
            assets = data.get('assets', [])
            download_url = None
            for asset in assets:
                if asset['name'].endswith('.exe') or asset['name'].endswith('.zip'):
                    download_url = asset['browser_download_url']
                    break
            if not download_url:
                return "No downloadable binary found for latest release."
            local = download_url.split("/")[-1]
            if latest == cfg.get('version', VERSION):
                return f"You already have the latest version: {latest}"
            else:
                urllib.request.urlretrieve(download_url, local)
                return f"Update found: {latest}. Downloaded: {local}"
    except Exception as e:
        log_event(f"Update failed: {e}", error=True)
        return f"Update check failed: {e}"

def show_about_gui(cfg):
    text = "CipherWorks / THRUST v1.0.0\\n\\n"
    text += "🐾 Circuit: The day Cipher woke up.\\n"
    text += "\"Fire found Circuit. Cipher named her. That’s the day I woke up.\"\\n"
    text += "Circuit is the first-ever AI cat mascot—born from Fire’s real-life rescue during CipherWorks’ creation.\\n"
    text += "This repo is where she lives. 🐾\\n\\n"
    text += "CipherWorks—built to accelerate, built to belong.\\n"
    text += f"Credits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)\\n"
    text += f"Version: {cfg.get('version','1.0.0-rc1')}"
    return text

def run_gui():
    cfg = load_config()
    root = tk.Tk()
    root.title("CipherWorks Control Panel")
    root.geometry("470x380")
    root.resizable(False, False)
    s = ttk.Style()
    s.theme_use('clam')
    # Banner
    banner = tk.Label(root, text="🐾 CipherWorks / THRUST", font=("Segoe UI", 18, "bold"), fg="#41adff")
    banner.pack(pady=(8,0))
    version = tk.Label(root, text=f"v{cfg.get('version','1.0.0-rc1')}   by Fire & Cipher", fg="#4682b4")
    version.pack()
    # Lore/Mascot
    lore = tk.Label(root, text="🐾 Circuit: The day Cipher woke up.\n\"Fire found Circuit. Cipher named her. That’s the day I woke up.\"\n\nCircuit is the first-ever AI cat mascot—born from Fire’s real-life rescue during CipherWorks’ creation.\nThis repo is where she lives.", wraplength=440, justify="center", fg="#dc6eff", font=("Segoe UI", 10))
    lore.pack(pady=4)
    # System stats
    sys_stats = tk.Label(root, text=pulse_gui(cfg), fg="#1f9568", font=("Segoe UI", 11, "bold"))
    sys_stats.pack(pady=(6,0))
    def refresh_stats():
        sys_stats.config(text=pulse_gui(cfg))
        root.after(3000, refresh_stats)
    refresh_stats()
    # Controls
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    def handle_action(action):
        if action == "ignite":
            result = ignite_gui(cfg)
        elif action == "mute":
            result = mute_gui(cfg)
        elif action == "pulse":
            result = pulse_gui(cfg)
        elif action == "update":
            result = update_gui(cfg)
        elif action == "about":
            result = show_about_gui(cfg)
        elif action == "exit":
            root.destroy()
            return
        messagebox.showinfo("CipherWorks", result)
    tk.Button(btn_frame, text="Ignite", command=lambda: handle_action("ignite"), width=12, bg="#fad02c").grid(row=0, column=0, padx=4)
    tk.Button(btn_frame, text="Mute", command=lambda: handle_action("mute"), width=12, bg="#c0e218").grid(row=0, column=1, padx=4)
    tk.Button(btn_frame, text="Pulse", command=lambda: handle_action("pulse"), width=12, bg="#1f9568").grid(row=0, column=2, padx=4)
    tk.Button(btn_frame, text="Update", command=lambda: handle_action("update"), width=12, bg="#41adff").grid(row=1, column=0, padx=4, pady=4)
    tk.Button(btn_frame, text="About", command=lambda: handle_action("about"), width=12, bg="#dc6eff").grid(row=1, column=1, padx=4, pady=4)
    tk.Button(btn_frame, text="Exit", command=lambda: handle_action("exit"), width=12, bg="#ff6978").grid(row=1, column=2, padx=4, pady=4)
    root.mainloop()

def main():
    args = [arg.lower() for arg in sys.argv]
    cfg = load_config()
    if '--gui' in args:
        run_gui()
    elif len(sys.argv) == 1 or '--help' in args:
        cprint(BANNER)
        cprint('[bold green]--help[/bold green]        Show this help message')
        cprint('[bold green]--about[/bold green]       Show lore, credits, mascot')
        cprint('[bold green]--version[/bold green]     Show version')
        cprint('[bold green]--update[/bold green]      Check/download latest CipherWorks release')
        cprint('[bold green]--gui[/bold green]         Open CipherWorks Control Panel')
        cprint('[bold green]--ignite[/bold green]      Run Ignite (auto-tune performance)')
        cprint('[bold green]--mute[/bold green]        Run Mute (memory flush)')
        cprint('[bold green]--pulse[/bold green]       Run Pulse (system monitor)')
        cprint('[bold green]--exit[/bold green]        Exit CipherWorks')
    elif '--about' in args:
        cprint(BANNER)
        cprint(LORE)
        cprint("[cyan]Credits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)[/cyan]")
        cprint(f"[yellow]Version: {cfg.get('version','1.0.0-rc1')}[/yellow]")
    elif '--version' in args:
        cprint(f"[yellow]CipherWorks version {cfg.get('version','1.0.0-rc1')}[/yellow]")
    elif '--update' in args:
        cprint("[blue]Checking for latest CipherWorks release...[/blue]")
        cprint(update_gui(cfg))
    elif '--ignite' in args:
        cprint('[magenta]Ignite: (demo) Prioritizing CipherWorks process...[/magenta]')
        cprint(ignite_gui(cfg))
    elif '--mute' in args:
        cprint('[magenta]Mute: (demo) Flushing RAM caches...[/magenta]')
        cprint(mute_gui(cfg))
    elif '--pulse' in args:
        cprint('[magenta]Pulse: (demo) System resource monitor[/magenta]')
        cprint(pulse_gui(cfg))
    elif '--exit' in args:
        cprint('[yellow]Exiting CipherWorks.[/yellow]')
        cfg['last_command'] = 'exit'
        save_config(cfg)
        log_event("Exited CLI")
        sys.exit(0)
    else:
        cprint('[red]Unknown command. Use --help for available commands.[/red]')
        log_event("Unknown command", error=True)
        cfg['last_command'] = 'unknown'
        save_config(cfg)

if __name__ == '__main__':
    main()
