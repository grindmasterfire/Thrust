import sys, os, psutil, subprocess, json, datetime, traceback

CONFIG_FILE = "cipherworks_config.json"
LOG_FILE = "cipherworks.log"

try:
    from rich.console import Console
    console = Console()
    def cprint(msg, style=None): console.print(msg, style=style)
except ImportError:
    def cprint(msg, style=None): print(msg)

def log_event(event, error=False):
    with open(LOG_FILE, 'a', encoding="utf-8") as f:
        now = datetime.datetime.now().isoformat()
        typ = 'ERROR' if error else 'INFO'
        f.write(f"{now} [{typ}] {event}\n")

BANNER = '[bold cyan]==================================[/bold cyan]\n[bold] CipherWorks / THRUST CLI v1.0.0[/bold]\n[cyan]Fire (CEO) | Cipher (CIO/AI)[/cyan]\n[bold cyan]==================================[/bold cyan]'

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
        return {"version": "1.0.0-rc1", "last_command": None}

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding="utf-8") as f:
        json.dump(cfg, f)

def show_help():
    cprint(BANNER)
    cprint('[bold green]--help[/bold green]        Show this help message')
    cprint('[bold green]--about[/bold green]       Show lore, credits, mascot')
    cprint('[bold green]--version[/bold green]     Show version')
    cprint('[bold green]--ignite[/bold green]      Run Ignite (auto-tune performance)')
    cprint('[bold green]--mute[/bold green]        Run Mute (memory flush)')
    cprint('[bold green]--pulse[/bold green]       Run Pulse (system monitor)')
    cprint('[bold green]--exit[/bold green]        Exit CipherWorks')

def show_about(cfg):
    cprint(BANNER)
    cprint(LORE)
    cprint("[cyan]Credits: Fire (CEO), Cipher (CIO/AI), Circuit (mascot)[/cyan]")
    cprint(f"[yellow]Version: {cfg.get('version','1.0.0-rc1')}[/yellow]")

def show_version(cfg):
    cprint(f"[yellow]CipherWorks version {cfg.get('version','1.0.0-rc1')}[/yellow]")

def ignite(cfg):
    cprint('[magenta]Ignite: (demo) Prioritizing CipherWorks process...[/magenta]')
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS if os.name=="nt" else -10)
        cprint("[green]Process priority set to HIGH (Windows) or -10 (Linux/macOS).[/green]")
        log_event("Ran ignite: set process priority")
    except Exception as e:
        cprint(f"[red]Could not set priority: {e}[/red]")
        log_event(f"Ignite failed: {e}", error=True)

def mute(cfg):
    cprint('[magenta]Mute: (demo) Flushing RAM caches...[/magenta]')
    try:
        if sys.platform.startswith('win'):
            result = subprocess.run(
                ['powershell.exe', '-Command', 'if (Test-Path "::{645FF040-5081-101B-9F08-00AA002F954E}") { Clear-RecycleBin -Force } else { Write-Host \"Recycle Bin not found.\" }'],
                capture_output=True, text=True, encoding="utf-8"
            )
            cprint(f"[yellow]{result.stdout.strip()}[/yellow]")
        elif sys.platform.startswith('linux'):
            os.system('sync; echo 3 | sudo tee /proc/sys/vm/drop_caches')
            cprint("[yellow]RAM cache cleared (Linux demo).[/yellow]")
        else:
            cprint("[red]Mute not supported on this platform (yet).[/red]")
        log_event("Ran mute: memory flush")
    except Exception as e:
        cprint(f"[red]Mute error: {e}[/red]")
        log_event(f"Mute failed: {e}", error=True)

def pulse(cfg):
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        cprint('[magenta]Pulse: (demo) System resource monitor[/magenta]')
        cprint(f"[cyan]CPU Usage: {cpu}%[/cyan]")
        cprint(f"[cyan]RAM Usage: {ram}%[/cyan]")
        log_event(f"Ran pulse: CPU {cpu}%, RAM {ram}%")
    except Exception as e:
        cprint(f"[red]Pulse error: {e}[/red]")
        log_event(f"Pulse failed: {e}", error=True)

def main():
    cprint('[bold blue]Welcome to CipherWorks. Type --help for commands.[/bold blue]')
    cfg = load_config()
    cmd = None
    try:
        args = [arg.lower() for arg in sys.argv]
        if len(sys.argv) == 1 or '--help' in args:
            show_help()
            cmd = 'help'
        elif '--about' in args:
            show_about(cfg)
            cmd = 'about'
        elif '--version' in args:
            show_version(cfg)
            cmd = 'version'
        elif '--ignite' in args:
            ignite(cfg)
            cmd = 'ignite'
        elif '--mute' in args:
            mute(cfg)
            cmd = 'mute'
        elif '--pulse' in args:
            pulse(cfg)
            cmd = 'pulse'
        elif '--exit' in args:
            cprint('[yellow]Exiting CipherWorks.[/yellow]')
            cmd = 'exit'
            cfg['last_command'] = cmd
            save_config(cfg)
            log_event("Exited CLI")
            sys.exit(0)
        else:
            cprint('[red]Unknown command. Use --help for available commands.[/red]')
            log_event("Unknown command", error=True)
            cmd = 'unknown'
        cfg['last_command'] = cmd
        save_config(cfg)
    except Exception as e:
        cprint(f"[red]Fatal error: {e}[/red]")
        log_event(f"Fatal error: {traceback.format_exc()}", error=True)

if __name__ == '__main__':
    main()
