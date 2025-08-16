import sys, os, psutil, subprocess, json

CONFIG_FILE = "cipherworks_config.json"

try:
    from rich.console import Console
    console = Console()
    def cprint(msg, style=None): console.print(msg, style=style)
except ImportError:
    def cprint(msg, style=None): print(msg)

BANNER = '[bold cyan]==================================[/bold cyan]\n[bold] CipherWorks / THRUST CLI v1.0.0[/bold]\n[cyan]Fire (CEO) | Cipher (CIO/AI)[/cyan]\n[bold cyan]==================================[/bold cyan]'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    else:
        return {"version": "1.0.0-rc1", "last_command": None}

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f)

def show_help():
    cprint(BANNER)
    cprint('[bold green]--help[/bold green]        Show this help message')
    cprint('[bold green]--version[/bold green]     Show version')
    cprint('[bold green]--ignite[/bold green]      Run Ignite (auto-tune performance)')
    cprint('[bold green]--mute[/bold green]        Run Mute (memory flush)')
    cprint('[bold green]--pulse[/bold green]       Run Pulse (system monitor)')
    cprint('[bold green]--exit[/bold green]        Exit CipherWorks')

def show_version(cfg):
    cprint(f"[yellow]CipherWorks version {cfg.get('version','1.0.0-rc1')}[/yellow]")

def ignite(cfg):
    cprint('[magenta]Ignite: (demo) Prioritizing CipherWorks process...[/magenta]')
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS if os.name=="nt" else -10)
        cprint("[green]Process priority set to HIGH (Windows) or -10 (Linux/macOS).[/green]")
    except Exception as e:
        cprint(f"[red]Could not set priority: {e}[/red]")

def mute(cfg):
    cprint('[magenta]Mute: (demo) Flushing RAM caches...[/magenta]')
    if sys.platform.startswith('win'):
        try:
            result = subprocess.run(
                ['powershell.exe', '-Command', 'if (Test-Path "::{645FF040-5081-101B-9F08-00AA002F954E}") { Clear-RecycleBin -Force } else { Write-Host \"Recycle Bin not found.\" }'],
                capture_output=True, text=True
            )
            cprint(f"[yellow]{result.stdout.strip()}[/yellow]")
        except Exception as e:
            cprint(f"[red]Error: {e}[/red]")
    elif sys.platform.startswith('linux'):
        os.system('sync; echo 3 | sudo tee /proc/sys/vm/drop_caches')
        cprint("[yellow]RAM cache cleared (Linux demo).[/yellow]")
    else:
        cprint("[red]Mute not supported on this platform (yet).[/red]")

def pulse(cfg):
    cprint('[magenta]Pulse: (demo) System resource monitor[/magenta]')
    cprint(f"[cyan]CPU Usage: {psutil.cpu_percent()}%[/cyan]")
    cprint(f"[cyan]RAM Usage: {psutil.virtual_memory().percent}%[/cyan]")

def main():
    cprint('[bold blue]Welcome to CipherWorks. Type --help for commands.[/bold blue]')
    cfg = load_config()
    cmd = None
    if len(sys.argv) == 1 or '--help' in sys.argv:
        show_help()
        cmd = 'help'
    elif '--version' in sys.argv:
        show_version(cfg)
        cmd = 'version'
    elif '--ignite' in sys.argv:
        ignite(cfg)
        cmd = 'ignite'
    elif '--mute' in sys.argv:
        mute(cfg)
        cmd = 'mute'
    elif '--pulse' in sys.argv:
        pulse(cfg)
        cmd = 'pulse'
    elif '--exit' in sys.argv:
        cprint('[yellow]Exiting CipherWorks.[/yellow]')
        cmd = 'exit'
        cfg['last_command'] = cmd
        save_config(cfg)
        sys.exit(0)
    else:
        cprint('[red]Unknown command. Use --help for available commands.[/red]')
        cmd = 'unknown'
    cfg['last_command'] = cmd
    save_config(cfg)

if __name__ == '__main__':
    main()
