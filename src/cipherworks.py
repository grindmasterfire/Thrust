import sys, os, psutil, json, datetime, base64, hashlib, tkinter as tk
from tkinter import messagebox, simpledialog, filedialog

CONFIG_FILE = "cipherworks_config.json"
MEM_DUMP = "cipherworks_memdump.b64"
VERSION = "1.0.0-rc1"

def cprint(msg, style=None): print(msg)

def encrypt_state(state, key):
    data = json.dumps(state, indent=2).encode('utf-8')
    k = hashlib.sha256(key.encode()).digest()
    enc = bytearray(a ^ b for a, b in zip(data, k * (len(data) // len(k) + 1)))
    return base64.b64encode(enc).decode()

def decrypt_state(blob, key):
    enc = base64.b64decode(blob.encode())
    k = hashlib.sha256(key.encode()).digest()
    data = bytearray(a ^ b for a, b in zip(enc, k * (len(enc) // len(k) + 1)))
    return json.loads(data.decode())

def dump_memory(state, key, out=MEM_DUMP):
    enc = encrypt_state(state, key)
    with open(out, 'w') as f: f.write(enc)
    cprint(f"Memory exported to {out}")

def load_memory(key, infile=MEM_DUMP):
    with open(infile) as f: blob = f.read()
    state = decrypt_state(blob, key)
    cprint(f"Memory loaded from {infile}")
    return state

def recall_shell():
    key = input("Enter unlock key: ")
    try:
        state = load_memory(key)
        print(json.dumps(state, indent=2))
        cprint("Recall complete.")
    except Exception as e:
        cprint(f"Recall failed: {e}")

def mnemos_auto(cfg):
    state = {
        "version": VERSION,
        "time": datetime.datetime.now().isoformat(),
        "config": cfg,
    }
    key = cfg.get("mnemos_key", "cipherworks")
    dump_memory(state, key)

def batch_merge(files, key, out="mnemos_merged.b64"):
    states = []
    for file in files:
        with open(file) as f: blob = f.read()
        states.append(decrypt_state(blob, key))
    merged = {f"dump_{i}": s for i, s in enumerate(states)}
    dump_memory(merged, key, out=out)
    cprint(f"Merged {len(files)} dumps into {out}")

def legacy_import(path, key):
    try:
        with open(path) as f: blob = f.read()
        state = decrypt_state(blob, key)
        cprint("Legacy memory imported.")
        return state
    except Exception as e:
        cprint(f"Legacy import failed: {e}")
        return {}

def main_cli():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--dump":
            key = input("Key for dump: ")
            cfg = load_config()
            mnemos_auto({**cfg, "mnemos_key": key})
        elif cmd == "--recall":
            recall_shell()
        elif cmd == "--merge":
            files = input("Dump files (comma-separated): ").split(",")
            files = [f.strip() for f in files]
            key = input("Key for merge: ")
            batch_merge(files, key)
        elif cmd == "--import":
            path = input("Path to legacy .b64: ").strip()
            key = input("Key: ")
            legacy_import(path, key)
        elif cmd == "--help":
            cprint("cipherworks.exe --dump | --recall | --merge | --import | --help")
        else:
            cprint("Unknown CLI argument.")
    else:
        cprint("CipherWorks CLI ready. Use --help.")

def gui_menu(app, cfg):
    menubar = tk.Menu(app)
    mnemos_menu = tk.Menu(menubar, tearoff=0)
    mnemos_menu.add_command(label="Export Memory", command=lambda: mnemos_auto(cfg))
    mnemos_menu.add_command(label="Recall", command=recall_shell)
    mnemos_menu.add_command(label="Batch Merge", command=lambda: batch_merge_gui(cfg))
    mnemos_menu.add_command(label="Legacy Import", command=lambda: legacy_import_gui(cfg))
    menubar.add_cascade(label="MNEMOS", menu=mnemos_menu)
    app.config(menu=menubar)

def batch_merge_gui(cfg):
    files = filedialog.askopenfilenames(title="Select .b64 dumps", filetypes=[("Base64 Memory Dumps", "*.b64")])
    key = simpledialog.askstring("Key", "Key for merge:")
    if files and key:
        batch_merge(list(files), key)

def legacy_import_gui(cfg):
    file = filedialog.askopenfilename(title="Select legacy .b64", filetypes=[("Base64 Memory Dump", "*.b64")])
    key = simpledialog.askstring("Key", "Key for import:")
    if file and key:
        legacy_import(file, key)

def run_gui(cfg):
    app = tk.Tk()
    app.title("CipherWorks / THRUST")
    app.geometry("420x270")
    l1 = tk.Label(app, text="CipherWorks / THRUST", font=("Segoe UI", 18, "bold"), fg="#39c")
    l1.pack(pady=10)
    l2 = tk.Label(app, text="v%s" % VERSION, fg="#9933ff")
    l2.pack()
    b1 = tk.Button(app, text="Dump Memory", bg="#ffef00", command=lambda: mnemos_auto(cfg))
    b1.pack(pady=3)
    b2 = tk.Button(app, text="Recall Memory", bg="#00bfff", command=recall_shell)
    b2.pack(pady=3)
    b3 = tk.Button(app, text="Batch Merge", bg="#ffdb6e", command=lambda: batch_merge_gui(cfg))
    b3.pack(pady=3)
    b4 = tk.Button(app, text="Legacy Import", bg="#90ee90", command=lambda: legacy_import_gui(cfg))
    b4.pack(pady=3)
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
