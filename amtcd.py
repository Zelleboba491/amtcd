import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os, configparser, random

CFG = "AmTCD.ini"; FT = [("TXTX","*.txtx"),("Все","*.*")]; TTL = "Смирнов Блокнот Практика 3"
C = {"bg":"#2c3e50","b2":"#34495e","b3":"#1e272e","fg":"#ecf0f1",
     "ac":"#3498db","a2":"#2980b9","gr":"#27ae60","rd":"#e74c3c","dm":"#95a5a6"}

# ── Крипто ──────────────────────────────────────────────────
def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    i = 3
    while i * i <= n:
        if n % i == 0: return False
        i += 2
    return True

def rand_prime():
    while True:
        n = random.randint(2, 10_000_000)
        if is_prime(n): return n

def parse_key(s):
    s = s.strip().replace(" ","").replace("\u00a0","")
    return int(s) if s.isdigit() else None

def xor_crypt(text, key):
    a, c, m, st = 1664525, 1013904223, 2**32, key % (2**32)
    out = []
    for ch in text:
        st = (a * st + c) % m; out.append(chr(ord(ch) ^ ((st % 127) + 1)))
    return "".join(out)

def fingerprint(enc, p, s):
    v = p * s
    for ch in enc: v = (v * 31 + ord(ch)) % (10**26)
    return str(v).zfill(26)

# ── Файлы / конфиг ──────────────────────────────────────────
def file_save(path, enc, fp, ses):
    cfg = configparser.ConfigParser()
    cfg["main"] = {"keyopen": fp, "session": str(ses), "mess": enc.encode("utf-16-le").hex()}
    cfg.write(open(path, "w", encoding="utf-8"))

def file_load(path):
    cfg = configparser.ConfigParser(); cfg.read(path, encoding="utf-8")
    return bytes.fromhex(cfg["main"]["mess"]).decode("utf-16-le"), cfg["main"]["keyopen"], int(cfg["main"]["session"])

def cfg_load():
    cfg = configparser.ConfigParser()
    if os.path.exists(CFG): cfg.read(CFG, encoding="utf-8")
    n = parse_key(cfg.get("main", "keyuser", fallback=""))
    return (n if n and is_prime(n) else None), cfg

def cfg_save(cfg, key):
    if "main" not in cfg: cfg["main"] = {}
    cfg["main"]["keyuser"] = str(key); cfg.write(open(CFG, "w", encoding="utf-8"))

# ── UI-хелперы ───────────────────────────────────────────────
def mkbtn(parent, text, cmd, **kw):
    b = tk.Button(parent, text=text, command=cmd, relief="flat", cursor="hand2",
                  bg=kw.pop("bg", C["b2"]), fg=kw.pop("fg", C["fg"]),
                  activebackground=kw.pop("abg", C["ac"]), activeforeground="white", **kw)
    b.pack(side="left", padx=1, pady=2); return b

def setup_tab(ws):
    orig = {w: w.cget("bg") for w in ws}
    for w in ws:
        w.config(takefocus=True)
        w.bind("<FocusIn>",  lambda e, w=w: w.config(bg="#4a6fa5"), add="+")
        w.bind("<FocusOut>", lambda e, w=w: w.config(bg=orig[w]),   add="+")
    for i, w in enumerate(ws):
        n, p = ws[(i+1)%len(ws)], ws[(i-1)%len(ws)]
        w.bind("<Tab>",       lambda e, n=n: (n.focus_set(),"break")[1], add="+")
        w.bind("<Shift-Tab>", lambda e, p=p: (p.focus_set(),"break")[1], add="+")

# ── Диалог «Параметры» ───────────────────────────────────────
class KeyDialog(tk.Toplevel):
    def __init__(self, parent, cur):
        super().__init__(parent); self.title("Параметры"); self.resizable(False,False)
        self.geometry("400x235"); self.configure(bg=C["bg"]); self.result = None
        tk.Label(self, text="Личный ключ (простое число 2–10 000 000):",
                 bg=C["bg"], fg=C["fg"]).pack(anchor="w", padx=14, pady=(12,3))
        self._var = tk.StringVar(value=str(cur) if cur else "")
        r = tk.Frame(self, bg=C["bg"]); r.pack(padx=14, fill="x")
        self._ent = tk.Entry(r, textvariable=self._var, font=("Consolas",11),
                             bg=C["b2"], fg=C["fg"], insertbackground="white", relief="flat", bd=4)
        self._ent.pack(side="left", fill="x", expand=True); self._ent.bind("<KeyRelease>", self._chk)
        mkbtn(r, "📋", lambda: self._clip(self._var), bg=C["b2"], fg=C["fg"], abg=C["ac"], font=("TkDefaultFont",11), padx=4)
        self._hint = tk.Label(self, text="", bg=C["bg"], fg=C["dm"], font=("TkDefaultFont",9), anchor="w")
        self._hint.pack(anchor="w", padx=14, pady=(2,0))
        self._err = tk.Label(self, text="", bg=C["bg"], fg=C["rd"], anchor="w")
        self._err.pack(anchor="w", padx=14)
        # Генератор
        gf = tk.Frame(self, bg=C["b2"]); gf.pack(fill="x", padx=14, pady=(6,0))
        tk.Label(gf, text="Случайный ключ:", bg=C["b2"], fg=C["dm"], font=("TkDefaultFont",9)).pack(anchor="w", padx=8, pady=(5,2))
        gr = tk.Frame(gf, bg=C["b2"]); gr.pack(fill="x", padx=8, pady=(0,6))
        self._gen = tk.StringVar(value=str(rand_prime()))
        tk.Entry(gr, textvariable=self._gen, font=("Consolas",11), bg=C["b3"], fg=C["gr"], relief="flat", bd=4, state="readonly").pack(side="left", fill="x", expand=True)
        mkbtn(gr, "📋", lambda: self._clip(self._gen), bg=C["b3"], fg=C["fg"], abg=C["ac"], font=("TkDefaultFont",11), padx=4)
        mkbtn(gr, "↻",  lambda: self._gen.set(str(rand_prime())), bg=C["ac"], fg="white", abg=C["a2"], font=("TkDefaultFont",13,"bold"), padx=6)
        mkbtn(gr, "Использовать", lambda: [self._var.set(self._gen.get()), self._chk()], bg=C["ac"], fg="white", abg=C["a2"])
        # Кнопки
        bf = tk.Frame(self, bg=C["bg"]); bf.pack(side="bottom", fill="x", padx=14, pady=10)
        bs = tk.Button(bf, text="Сохранить", width=11, command=self._save, bg=C["ac"], fg="white", activebackground=C["a2"], relief="flat", cursor="hand2")
        bc = tk.Button(bf, text="Отмена",    width=9,  command=self.destroy, bg=C["b2"], fg=C["fg"], activebackground=C["bg"], relief="flat", cursor="hand2")
        bs.pack(side="right"); bc.pack(side="right", padx=(0,6))
        setup_tab([self._ent, bs, bc]); self.transient(parent); self.grab_set()
        self._ent.focus_set(); self._ent.bind("<Return>", lambda e: self._save()); self.bind("<Escape>", lambda e: self.destroy()); parent.wait_window(self)

    def _clip(self, v): self.clipboard_clear(); self.clipboard_append(v.get())
    def _chk(self, _=None):
        n = parse_key(self._var.get()); self._err.config(text="")
        if   n is None:          self._hint.config(text="Только цифры" if self._var.get().strip() else "", fg=C["rd"]); return
        if   not(2<=n<=10_000_000): self._hint.config(text="От 2 до 10 000 000", fg=C["rd"])
        elif is_prime(n):        self._hint.config(text=f"✓ {n} — простое", fg=C["gr"])
        else:                    self._hint.config(text=f"✗ {n} — не простое", fg=C["rd"])
    def _save(self):
        n = parse_key(self._var.get())
        if   n is None:             self._err.config(text="Введите целое число"); return
        if   not(2<=n<=10_000_000): self._err.config(text="От 2 до 10 000 000"); return
        if   not is_prime(n):       self._err.config(text=f"{n} — не простое"); return
        self.result = n; self.destroy()

# ── Главное окно ─────────────────────────────────────────────
class App:
    def __init__(self, root):
        self.root = root; self.file = None; self.dirty = False; self._hw = None
        root.geometry("700x500"); root.minsize(500, 360)
        self._key, self._cfg = cfg_load()
        self._build_menu(); self._build_ui(); self._apply_theme()
        for k, c in [("<Control-n>",self.cmd_new),("<Control-o>",self.cmd_open),
                     ("<Control-s>",self.cmd_save),("<Control-q>",self.cmd_quit),("<F1>",self.cmd_help)]:
            root.bind_all(k, lambda e, c=c: c())
        self._upd()

    def _build_menu(self):
        mb = tk.Menu(self.root, bg=C["bg"], fg=C["fg"], activebackground=C["ac"], activeforeground="white")
        def menu(label, items):
            m = tk.Menu(mb, tearoff=0, bg=C["b2"], fg=C["fg"], activebackground=C["ac"], activeforeground="white")
            for it in items:
                if it is None: m.add_separator()
                else: m.add_command(label=it[0], accelerator=it[1] if len(it)>2 else "", command=it[-1])
            mb.add_cascade(label=label, menu=m)
        menu("Файл",    [("Новый","Ctrl+N",self.cmd_new),("Открыть","Ctrl+O",self.cmd_open),
                         ("Сохранить","Ctrl+S",self.cmd_save),("Сохранить как...",self.cmd_saveas),
                         None,("Выход","Ctrl+Q",self.cmd_quit)])
        menu("Правка",  [("Копировать","Ctrl+C",lambda:self.ta.event_generate("<<Copy>>")),
                         ("Вставить","Ctrl+V",lambda:self.ta.event_generate("<<Paste>>")),
                         None,("Параметры...",self.cmd_key)])
        menu("Справка", [("Содержание","F1",self.cmd_help),("О программе...",self.cmd_about)])
        self.root.config(menu=mb)

    def _build_ui(self):
        tb = tk.Frame(self.root, bg=C["b2"], height=28); tb.pack(fill="x"); tb.pack_propagate(False)
        tbs = [mkbtn(tb,lbl,cmd) for lbl,cmd in [("📄 Новый",self.cmd_new),("📂 Открыть",self.cmd_open),
               ("💾 Сохранить",self.cmd_save),("🔑 Ключ",self.cmd_key),("❓ Справка",self.cmd_help),("ℹ О программе",self.cmd_about)]]
        self.ta = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, font=("Consolas",11),
            bg=C["b3"], fg=C["fg"], insertbackground="white", selectbackground=C["ac"], relief="flat", padx=6, pady=4)
        self.ta.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4,0)); self.ta.bind("<<Modified>>", lambda e: self._on_mod())
        sb = tk.Frame(self.root, bg=C["b3"], height=22); sb.pack(fill="x", side="bottom")
        self._st = tk.StringVar(value="Готово"); self._kv = tk.StringVar()
        for v, s in [(self._st,"left"),(self._kv,"right")]:
            tk.Label(sb, textvariable=v, bg=C["b3"], fg=C["dm"], font=("TkDefaultFont",9), padx=6).pack(side=s)
        setup_tab(tbs + [self.ta])

    def _apply_theme(self):
        try: ttk.Style().theme_use("clam")
        except: pass
        self.root.configure(bg=C["bg"])
        try: self.root.iconbitmap("AmTCD.ico")
        except: pass

    def _upd(self):
        name = os.path.basename(self.file) if self.file else "NoName.txtx"
        self.root.title(f"{name}{' *' if self.dirty else ''} — {TTL}")
        self._kv.set(f"Ключ: {self._key}" if self._key else "Ключ: не задан")

    def _on_mod(self):
        if self.ta.edit_modified(): self.dirty = True; self._upd(); self.ta.edit_modified(False)

    def _guard(self):
        if not self.dirty: return True
        r = messagebox.askyesnocancel("AmTCD", "Сохранить изменения?")
        if r is None: return False
        if r: self.cmd_save()
        return True

    def _need_key(self):
        if self._key: return True
        messagebox.showwarning("Ключ не задан", "Задайте ключ: Правка → Параметры"); return False

    def cmd_new(self):
        if not self._guard(): return
        self.ta.delete(1.0, tk.END); self.ta.edit_reset()
        self.file = None; self.dirty = False; self._st.set("Новый файл"); self._upd()

    def cmd_open(self):
        if not self._guard() or not self._need_key(): return
        path = filedialog.askopenfilename(title="Открыть", filetypes=FT, defaultextension=".txtx")
        if not path: return
        try:
            enc, fp, ses = file_load(path)
            if fingerprint(enc, self._key, ses) != fp:
                messagebox.showerror("Ошибка ключа", "Неверный ключ или файл повреждён."); return
            self.ta.delete(1.0, tk.END); self.ta.insert(1.0, xor_crypt(enc, self._key * ses))
            self.ta.edit_reset(); self.file = path; self.dirty = False
            self._st.set(f"Открыт: {os.path.basename(path)}"); self._upd()
        except Exception as ex: messagebox.showerror("Ошибка", str(ex))

    def cmd_save(self):
        (self._write(self.file) if self.file else self.cmd_saveas())

    def cmd_saveas(self):
        p = filedialog.asksaveasfilename(title="Сохранить как", filetypes=FT, defaultextension=".txtx")
        if p: self._write(p)

    def _write(self, path):
        if not self._need_key(): return
        ses = rand_prime(); enc = xor_crypt(self.ta.get(1.0, "end-1c"), self._key * ses)
        try:
            file_save(path, enc, fingerprint(enc, self._key, ses), ses)
            self.file = path; self.dirty = False
            self._st.set(f"Сохранён: {os.path.basename(path)}  [сессия: {ses}]"); self._upd()
        except Exception as ex: messagebox.showerror("Ошибка", str(ex))

    def cmd_quit(self):
        if self._guard(): self.root.destroy()

    def cmd_key(self):
        d = KeyDialog(self.root, self._key)
        if d.result:
            self._key = d.result; cfg_save(self._cfg, d.result)
            self._st.set(f"Ключ {d.result} сохранён"); self._upd()

    def cmd_help(self):
        if self._hw and self._hw.winfo_exists(): self._hw.lift(); self._hw.focus_set(); return
        h = tk.Toplevel(self.root); h.title("Справка"); h.geometry("420x310"); h.configure(bg=C["bg"]); self._hw = h
        t = scrolledtext.ScrolledText(h, wrap=tk.WORD, bg=C["b2"], fg=C["fg"],
                                      insertbackground="white", relief="flat", padx=8, pady=6)
        t.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8,4))
        t.insert(1.0, "Блокнот AmTCD v2.0\n\nШифрование:\n"
            "  • Личный ключ — простое число 2–10 000 000 (AmTCD.ini)\n"
            "  • Сессионный ключ — случайное простое при каждом сохранении\n"
            "  • Итоговый ключ = личный × сессионный\n\n"
            "Горячие клавиши:\n"
            "  Ctrl+N  Новый       Ctrl+O  Открыть\n"
            "  Ctrl+S  Сохранить   Ctrl+Q  Выход\n"
            "  F1      Справка     Tab     Навигация\n\n"
            "──────────────────────────────────────\n"
            "(С) Смирнов Л.Д.\n"
            "Спасибо Елене Викторовне и Денису Владимировичу за воспитание\n")
        t.config(state=tk.DISABLED)
        tk.Button(h, text="Закрыть", command=h.destroy, bg=C["ac"], fg="white",
                  activebackground=C["a2"], relief="flat", cursor="hand2").pack(pady=(2,10))

    def cmd_about(self):
        d = tk.Toplevel(self.root); d.title("О программе"); d.geometry("330x110")
        d.resizable(False,False); d.configure(bg=C["bg"])
        f = tk.Frame(d, bg=C["bg"], padx=14, pady=14); f.pack(fill="both", expand=True)
        tk.Label(f, text="i", font=("TkDefaultFont",20,"bold"), bg=C["ac"], fg="white", width=2, relief="flat").grid(row=0, column=0, padx=(0,12), sticky="n")
        tk.Label(f, text="Программа для 'прозрачного шифрования'", bg=C["bg"], fg=C["fg"], anchor="w").grid(row=0, column=1, sticky="w")
        b = tk.Button(f, text="OK", command=d.destroy, width=8, bg=C["ac"], fg="white", activebackground=C["a2"], relief="flat", cursor="hand2")
        b.grid(row=1, column=0, columnspan=2, pady=(14,0), sticky="e")
        d.transient(self.root); d.grab_set(); b.focus_set()
        d.bind("<Return>", lambda e: d.destroy()); d.bind("<Escape>", lambda e: d.destroy()); self.root.wait_window(d)

if __name__ == "__main__":
    root = tk.Tk(); app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.cmd_quit); root.mainloop()