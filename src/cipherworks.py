import sys, os, psutil

BANNER = '''
==================================
 CipherWorks / THRUST CLI v1.0.0
 Fire (CEO) | Cipher (CIO/AI)
==================================
'''

def show_help():
    print(BANNER)
    print('--help        Show this help message')
    print('--version     Show version')
    print('--ignite      Run Ignite (auto-tune performance)')
    print('--mute        Run Mute (memory flush)')
    print('--pulse       Run Pulse (system monitor)')
    print('--exit        Exit CipherWorks')

def show_version():
    print('CipherWorks version 1.0.0-rc1')

def ignite():
    print('Ignite: (demo) Prioritizing CipherWorks process...')
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS if os.name=="nt" else -10)
        print("Process priority set to HIGH (Windows) or -10 (Linux/macOS).")
    except Exception as e:
        print(f"Could not set priority: {e}")

def mute():
    print('Mute: (demo) Flushing RAM caches...')
    if sys.platform.startswith('win'):
        os.system('powershell.exe Clear-RecycleBin -Force')
        print("Recycle Bin cleared (Windows demo).")
    elif sys.platform.startswith('linux'):
        os.system('sync; echo 3 | sudo tee /proc/sys/vm/drop_caches')
        print("RAM cache cleared (Linux demo).")
    else:
        print("Mute not supported on this platform (yet).")

def pulse():
    print('Pulse: (demo) System resource monitor')
    print(f"CPU Usage: {psutil.cpu_percent()}%")
    print(f"RAM Usage: {psutil.virtual_memory().percent}%")

def main():
    if len(sys.argv) == 1 or '--help' in sys.argv:
        show_help()
    elif '--version' in sys.argv:
        show_version()
    elif '--ignite' in sys.argv:
        ignite()
    elif '--mute' in sys.argv:
        mute()
    elif '--pulse' in sys.argv:
        pulse()
    elif '--exit' in sys.argv:
        print('Exiting CipherWorks.')
        sys.exit(0)
    else:
        print('Unknown command. Use --help for available commands.')

if __name__ == '__main__':
    main()
