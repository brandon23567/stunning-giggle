"""
Python Experiment 6: Student Management System using Tkinter
=============================================================
A multi-page desktop GUI that demonstrates the Tkinter toolkit:

  * Windows & layout : Tk, Toplevel, Frame, LabelFrame, PanedWindow, Notebook
  * Widgets          : Label, Button, Entry, Text, Listbox, Scrollbar, Checkbutton,
                       Radiobutton, Spinbox, Scale, OptionMenu, Menubutton, Message,
                       Canvas, Combobox, Treeview, Progressbar, Separator, Menu
  * Geometry         : pack(), grid(), place()
  * Styling          : colours, fonts, relief, borders, cursors, images, ttk.Style
  * Events           : bind(), command=, protocol(), after(), trace_add(), validatecommand
  * Dialogs          : messagebox, filedialog, simpledialog, colorchooser
  * Navigation       : stacked frames + tkraise(), sidebar, menu bar, keyboard shortcuts

Run :  python experiment6_student_management.py
Login: admin / admin123
Data is stored in students.json (created next to this script on first run).
"""

import csv
import json
import os
import random
import re
import shutil
import tkinter as tk
import tkinter.font as tkfont
from collections import Counter
from datetime import datetime
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser

# ----------------------------------------------------------------------------
# CONSTANTS & SMALL HELPERS
# ----------------------------------------------------------------------------
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.json")

SUBJECTS = ["Maths", "Physics", "Programming", "English"]
COURSES = ["B.Tech CSE", "B.Tech ECE", "B.Tech ME", "BCA", "MCA", "B.Sc Physics"]
SKILLS = ["Python", "Java", "C/C++", "Web Dev", "Data Science",
          "Public Speaking", "Sports", "Music"]
SCHOLARSHIPS = ["None", "Merit", "Sports", "Need-based"]
CHART_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#8b5cf6"]

BG = "#f4f6fb"          # window background
CARD = "#ffffff"        # card / panel background
TEXT = "#1f2937"
MUTED = "#6b7280"
FONT = "Segoe UI"       # falls back automatically if not installed

ACCENT_PRESETS = {"Indigo": "#4f46e5", "Teal": "#0d9488",
                  "Rose": "#e11d48", "Slate": "#475569"}


def darken(hex_color, factor=0.6):
    """Return a darker shade of a #rrggbb colour."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def grade_for(pct):
    for limit, g in [(90, "A+"), (80, "A"), (70, "B+"), (60, "B"), (50, "C"), (40, "D")]:
        if pct >= limit:
            return g
    return "F"


def percentage(student):
    marks = student.get("marks", {})
    return sum(marks.values()) / len(SUBJECTS) if marks else 0.0


# ----------------------------------------------------------------------------
# DATA LAYER  (JSON file)
# ----------------------------------------------------------------------------
class DataStore:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.students = []
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    self.students = json.load(f)
                return
            except (json.JSONDecodeError, OSError):
                pass
        self.seed()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.students, f, indent=2)

    def seed(self):
        """Create realistic sample data the first time the app runs."""
        rnd = random.Random(7)
        names = ["Aarav Sharma", "Priya Verma", "Rohan Gupta", "Sneha Iyer",
                 "Karan Singh", "Ananya Das", "Vikram Rao", "Meera Nair",
                 "Arjun Patel", "Simran Kaur", "Rahul Mehta", "Isha Kapoor"]
        self.students = []
        for i, name in enumerate(names, start=1):
            first = name.split()[0].lower()
            ability = rnd.randint(30, 88)             # each student has a base ability
            self.students.append({
                "id": i, "name": name, "age": rnd.randint(18, 24),
                "gender": "Female" if first in ("priya", "sneha", "ananya", "meera",
                                                 "simran", "isha") else "Male",
                "email": f"{first}{i}@college.edu",
                "phone": "9" + "".join(str(rnd.randint(0, 9)) for _ in range(9)),
                "course": rnd.choice(COURSES), "semester": rnd.randint(1, 8),
                "scholarship": rnd.choice(SCHOLARSHIPS),
                "skills": rnd.sample(SKILLS, 3), "hostel": rnd.choice([True, False]),
                "address": f"{rnd.randint(1, 99)}, Model Town, Ludhiana",
                "marks": {s: max(5, min(100, ability + rnd.randint(-15, 15))) for s in SUBJECTS},
                "attendance": rnd.randint(62, 99),
            })
        self.save()

    def next_id(self):
        return max((s["id"] for s in self.students), default=0) + 1

    def get(self, sid):
        return next((s for s in self.students if s["id"] == sid), None)

    def add(self, student):
        self.students.append(student)
        self.save()

    def update(self, student):
        for i, s in enumerate(self.students):
            if s["id"] == student["id"]:
                self.students[i] = student
        self.save()

    def delete(self, sid):
        self.students = [s for s in self.students if s["id"] != sid]
        self.save()


# ----------------------------------------------------------------------------
# MAIN APPLICATION (root window)
# ----------------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Management System")
        self.geometry("1150x700+80+40")        # width x height + x_offset + y_offset
        self.minsize(980, 620)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        # shared state held in Tkinter variables
        self.store = DataStore()
        self.accent = ACCENT_PRESETS["Indigo"]
        self.pass_mark = tk.IntVar(value=40)
        self.confirm_delete = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Ready")
        self.accent_widgets = []               # (widget, role) re-coloured on theme change
        self.activity = []                     # recent activity log

        self.setup_fonts()
        self.setup_styles()

        self.main = None
        self.login = LoginPage(self, self)
        self.login.pack(fill="both", expand=True)

        self.bind_all("<Control-q>", lambda e: self.on_exit())

    # ------------------------------------------------------------ fonts/styles
    def setup_fonts(self):
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(name).configure(family=FONT, size=10)

    def setup_styles(self):
        """ttk widgets are styled through a Style object, not widget options."""
        st = ttk.Style(self)
        st.theme_use("clam")                   # 'clam' honours custom colours
        a = self.accent
        st.configure("Treeview", background=CARD, fieldbackground=CARD,
                     foreground=TEXT, rowheight=28, borderwidth=0)
        st.configure("Treeview.Heading", background=a, foreground="white",
                     font=(FONT, 10, "bold"), relief="flat", padding=6)
        st.map("Treeview.Heading", background=[("active", darken(a, 0.85))])
        st.map("Treeview", background=[("selected", "#c7d2fe")],
               foreground=[("selected", "#111827")])
        st.configure("TNotebook", background=BG, borderwidth=0)
        st.configure("TNotebook.Tab", padding=(16, 8), font=(FONT, 10, "bold"),
                     background="#e5e7eb", foreground=MUTED)
        st.map("TNotebook.Tab", background=[("selected", a)],
               foreground=[("selected", "white")])
        st.configure("TCombobox", padding=5, arrowsize=16)
        st.configure("Horizontal.TProgressbar", troughcolor="#e5e7eb",
                     background=a, thickness=14)
        st.configure("TSeparator", background="#d1d5db")
        st.configure("TPanedwindow", background=BG)

    # ------------------------------------------------------------ helpers
    def button(self, parent, text, command, kind="accent", **kw):
        """Factory for flat, coloured buttons with hover effect."""
        fixed = {"danger": "#e11d48", "success": "#10b981",
                 "neutral": "#64748b", "warn": "#f59e0b"}

        def base():
            return self.accent if kind == "accent" else fixed[kind]

        b = tk.Button(parent, text=text, command=command, fg="white", relief="flat",
                      bd=0, padx=14, pady=6, cursor="hand2",
                      font=(FONT, 10, "bold"), activeforeground="white", **kw)
        b.config(bg=base(), activebackground=darken(base(), 0.8))
        b.bind("<Enter>", lambda e: b["state"] != "disabled" and b.config(bg=darken(base(), 0.85)))
        b.bind("<Leave>", lambda e: b.config(bg=base()))
        if kind == "accent":
            self.accent_widgets.append((b, "button"))
        return b

    def entry(self, parent, var=None, **kw):
        e = tk.Entry(parent, textvariable=var, relief="flat", bg="#f9fafb", fg=TEXT,
                     insertbackground=TEXT, highlightthickness=1,
                     highlightbackground="#d1d5db", highlightcolor=self.accent,
                     font=(FONT, 10), **kw)
        self.accent_widgets.append((e, "entry"))
        return e

    def apply_accent(self, colour):
        self.accent = colour
        self.setup_styles()
        alive = []
        for w, role in self.accent_widgets:
            try:
                if role == "button":
                    w.config(bg=colour, activebackground=darken(colour, 0.8))
                elif role == "accent_bg":
                    w.config(bg=colour)
                elif role == "accent_fg":
                    w.config(fg=colour)
                elif role == "sidebar":
                    w.config(bg=darken(colour, 0.4))
                elif role == "entry":
                    w.config(highlightcolor=colour)
                alive.append((w, role))
            except tk.TclError:
                pass                              # widget was destroyed
        self.accent_widgets = alive
        if self.main:
            self.main.highlight_nav()
        self.set_status(f"Accent colour changed to {colour}")

    def set_status(self, msg):
        self.status.set(msg)
        self.after(5000, lambda: self.status.set("Ready"))

    def log(self, msg):
        self.activity.insert(0, f"{datetime.now():%H:%M}  {msg}")
        del self.activity[30:]

    # ------------------------------------------------------------ navigation
    def login_success(self, user):
        self.login.pack_forget()
        self.main = MainFrame(self, self, user)
        self.main.pack(fill="both", expand=True)
        self.config(menu=self.main.menubar)
        self.log(f"{user} logged in")
        self.main.show_page("dashboard")

    def logout(self):
        if messagebox.askyesno("Logout", "Do you really want to log out?"):
            self.main.destroy()
            self.main = None
            self.config(menu=tk.Menu(self))        # empty menu bar
            self.login.reset()
            self.login.pack(fill="both", expand=True)

    def on_exit(self):
        if messagebox.askokcancel("Exit", "Close the Student Management System?"):
            self.destroy()


# ----------------------------------------------------------------------------
# LOGIN PAGE  (place(), Entry show=, Checkbutton, after())
# ----------------------------------------------------------------------------
class LoginPage(tk.Frame):
    USER, PASSWORD = "admin", "admin123"

    def __init__(self, parent, app):
        super().__init__(parent, bg=app.accent)
        self.app = app
        app.accent_widgets.append((self, "accent_bg"))
        self.attempts = 0

        # place() with relative coordinates keeps the card centred when resizing
        card = tk.Frame(self, bg=CARD, padx=44, pady=32, highlightthickness=1,
                        highlightbackground="#e5e7eb")
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="🎓", font=(FONT, 38), bg=CARD).grid(row=0, column=0, columnspan=2)
        tk.Label(card, text="Student Management System", font=(FONT, 17, "bold"),
                 bg=CARD, fg=TEXT).grid(row=1, column=0, columnspan=2, pady=(0, 2))
        tk.Label(card, text="Sign in to continue", fg=MUTED, bg=CARD).grid(
            row=2, column=0, columnspan=2, pady=(0, 18))

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.show_var = tk.IntVar(value=0)

        tk.Label(card, text="Username", bg=CARD, fg=TEXT, anchor="w").grid(
            row=3, column=0, columnspan=2, sticky="w")
        self.user_entry = app.entry(card, self.user_var, width=32)
        self.user_entry.grid(row=4, column=0, columnspan=2, pady=(2, 10), ipady=6)

        tk.Label(card, text="Password", bg=CARD, fg=TEXT, anchor="w").grid(
            row=5, column=0, columnspan=2, sticky="w")
        self.pass_entry = app.entry(card, self.pass_var, width=32, show="•")
        self.pass_entry.grid(row=6, column=0, columnspan=2, pady=(2, 6), ipady=6)

        tk.Checkbutton(card, text="Show password", variable=self.show_var,
                       command=self.toggle_password, bg=CARD, fg=MUTED,
                       activebackground=CARD, cursor="hand2").grid(
            row=7, column=0, sticky="w")

        self.msg = tk.Label(card, text="", fg="#e11d48", bg=CARD)
        self.msg.grid(row=8, column=0, columnspan=2, pady=4)

        self.btn = app.button(card, "LOGIN", self.try_login)
        self.btn.grid(row=9, column=0, columnspan=2, sticky="ew", ipady=4)

        tk.Label(card, text="Demo credentials:  admin / admin123", fg=MUTED,
                 bg=CARD, font=(FONT, 9)).grid(row=10, column=0, columnspan=2, pady=(14, 0))

        self.bind_all("<Return>", self._enter_pressed)
        self.user_entry.focus_set()

    def _enter_pressed(self, _event):
        if self.winfo_ismapped():
            self.try_login()

    def toggle_password(self):
        self.pass_entry.config(show="" if self.show_var.get() else "•")

    def try_login(self):
        if str(self.btn["state"]) == "disabled":
            return
        if self.user_var.get() == self.USER and self.pass_var.get() == self.PASSWORD:
            self.app.login_success(self.user_var.get())
            return
        self.attempts += 1
        self.msg.config(text=f"Invalid credentials (attempt {self.attempts}/3)")
        if self.attempts >= 3:                       # lock the button for 5 seconds
            self.btn.config(state="disabled", bg="#9ca3af")
            self.msg.config(text="Too many attempts. Wait 5 seconds…")
            self.after(5000, self.unlock)

    def unlock(self):
        self.attempts = 0
        self.btn.config(state="normal", bg=self.app.accent)
        self.msg.config(text="")

    def reset(self):
        self.user_var.set("")
        self.pass_var.set("")
        self.msg.config(text="")
        self.user_entry.focus_set()


# ----------------------------------------------------------------------------
# MAIN FRAME: sidebar + header + stacked pages + status bar
# ----------------------------------------------------------------------------
class MainFrame(tk.Frame):
    NAV = [("dashboard", "🏠  Dashboard"), ("students", "👥  Students"),
           ("form", "➕  Add Student"), ("marks", "📝  Marks & Reports"),
           ("lab", "🧪  Widget Lab"), ("settings", "⚙️  Settings")]
    TITLES = {"dashboard": "Dashboard", "students": "Student Records",
              "form": "Student Form", "marks": "Marks & Reports",
              "lab": "Tkinter Widget Lab", "settings": "Settings"}

    def __init__(self, parent, app, user):
        super().__init__(parent, bg=BG)
        self.app, self.user = app, user

        self.build_menu()

        # ---- sidebar (pack, fixed width) --------------------------------
        self.sidebar = tk.Frame(self, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)           # keep fixed width
        app.accent_widgets.append((self.sidebar, "sidebar"))
        self.sidebar.config(bg=darken(app.accent, 0.4))

        logo = tk.Label(self.sidebar, text="🎓 EduManage", font=(FONT, 16, "bold"),
                        fg="white", pady=22)
        logo.pack(fill="x")
        app.accent_widgets.append((logo, "sidebar"))
        logo.config(bg=darken(app.accent, 0.4))

        self.nav_buttons = {}
        for key, text in self.NAV:
            b = tk.Button(self.sidebar, text=text, anchor="w", padx=22, pady=9,
                          fg="#e5e7eb", relief="flat", bd=0, cursor="hand2",
                          font=(FONT, 11), activeforeground="white",
                          command=lambda k=key: self.show_page(k))
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, b=b: b.config(fg="white"))
            b.bind("<Leave>", lambda e, b=b: b.config(fg="#e5e7eb"))
            self.nav_buttons[key] = b

        spacer = tk.Frame(self.sidebar)
        spacer.pack(fill="both", expand=True)
        app.accent_widgets.append((spacer, "sidebar"))
        spacer.config(bg=darken(app.accent, 0.4))

        who = tk.Label(self.sidebar, text=f"Signed in as  {user}", fg="#c7d2fe",
                       font=(FONT, 9))
        who.pack(pady=(0, 6))
        app.accent_widgets.append((who, "sidebar"))
        who.config(bg=darken(app.accent, 0.4))
        app.button(self.sidebar, "Logout", app.logout, kind="danger").pack(
            fill="x", padx=18, pady=(0, 18))

        # ---- right side: header, content, status bar -------------------------
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        header = tk.Frame(right, bg=CARD, height=62, highlightthickness=1,
                          highlightbackground="#e5e7eb")
        header.pack(fill="x")
        header.pack_propagate(False)
        self.title_lbl = tk.Label(header, text="", font=(FONT, 18, "bold"), bg=CARD)
        self.title_lbl.pack(side="left", padx=24)
        app.accent_widgets.append((self.title_lbl, "accent_fg"))
        self.clock = tk.Label(header, text="", font=(FONT, 11), bg=CARD, fg=MUTED)
        self.clock.pack(side="right", padx=24)

        status = tk.Label(right, textvariable=app.status, anchor="w", bg="#e5e7eb",
                          fg=MUTED, padx=12, pady=3, font=(FONT, 9))
        status.pack(side="bottom", fill="x")

        self.container = tk.Frame(right, bg=BG)
        self.container.pack(fill="both", expand=True, padx=20, pady=16)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # ---- create every page and stack them in the same grid cell -----------
        self.pages = {
            "dashboard": DashboardPage(self.container, app),
            "students": StudentsPage(self.container, app),
            "form": StudentFormPage(self.container, app),
            "marks": MarksPage(self.container, app),
            "lab": WidgetLabPage(self.container, app),
            "settings": SettingsPage(self.container, app),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.current = None
        self.tick()

    # ------------------------------------------------------------ menu bar
    def build_menu(self):
        app = self.app
        self.menubar = tk.Menu(app)

        file_m = tk.Menu(self.menubar, tearoff=0)
        file_m.add_command(label="New Student", accelerator="Ctrl+N",
                           command=lambda: self.new_student())
        file_m.add_command(label="Export to CSV…", command=lambda: self.pages["students"].export_csv())
        file_m.add_command(label="Backup data…", command=self.backup)
        file_m.add_separator()
        file_m.add_command(label="Logout", command=app.logout)
        file_m.add_command(label="Exit", accelerator="Ctrl+Q", command=app.on_exit)
        self.menubar.add_cascade(label="File", menu=file_m)

        view_m = tk.Menu(self.menubar, tearoff=0)
        for i, (key, text) in enumerate(self.NAV, start=1):
            view_m.add_command(label=text.strip(), accelerator=f"Ctrl+{i}",
                               command=lambda k=key: self.show_page(k))
            app.bind_all(f"<Control-Key-{i}>", lambda e, k=key: self.show_page(k))
        self.menubar.add_cascade(label="View", menu=view_m)

        # check / radio items inside a menu
        opt_m = tk.Menu(self.menubar, tearoff=0)
        opt_m.add_checkbutton(label="Confirm before delete", variable=app.confirm_delete)
        opt_m.add_separator()
        self.sort_var = tk.StringVar(value="name")
        for label in ("name", "course", "percentage"):
            opt_m.add_radiobutton(label=f"Default sort: {label}", variable=self.sort_var, value=label)
        self.menubar.add_cascade(label="Options", menu=opt_m)

        help_m = tk.Menu(self.menubar, tearoff=0)
        help_m.add_command(label="About", command=self.about)
        self.menubar.add_cascade(label="Help", menu=help_m)

        app.bind_all("<Control-n>", lambda e: self.new_student())

    def about(self):
        messagebox.showinfo(
            "About",
            "Student Management System\nPython Experiment 6 – Tkinter GUI\n\n"
            "Demonstrates widgets, geometry managers, styling,\nevents, dialogs and multi-page navigation.")

    def backup(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json", initialfile="students_backup.json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            shutil.copy(self.app.store.path, path)
            self.app.set_status(f"Backup saved to {path}")

    def new_student(self):
        self.pages["form"].load(None)
        self.show_page("form")

    # ------------------------------------------------------------ navigation
    def show_page(self, key):
        page = self.pages[key]
        page.tkraise()                                  # bring this frame to the front
        if hasattr(page, "on_show"):
            page.on_show()
        self.current = key
        self.title_lbl.config(text=self.TITLES[key])
        self.highlight_nav()

    def highlight_nav(self):
        for k, b in self.nav_buttons.items():
            if k == self.current:
                b.config(bg=self.app.accent, fg="white")
            else:
                b.config(bg=darken(self.app.accent, 0.4))

    def tick(self):
        """Update the clock every second using after()."""
        self.clock.config(text=datetime.now().strftime("%A, %d %B %Y   %H:%M:%S"))
        self._tick_id = self.after(1000, self.tick)

    def destroy(self):
        if hasattr(self, "_tick_id"):
            self.after_cancel(self._tick_id)
        super().destroy()


# ----------------------------------------------------------------------------
# DASHBOARD  (cards, Canvas drawing, Listbox, Progressbar)
# ----------------------------------------------------------------------------
class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        # --- stat cards (grid with equal column weights) ---------------------
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x")
        self.vars = {}
        specs = [("total", "Total Students", "#6366f1"), ("avg", "Average Marks", "#10b981"),
                 ("pass", "Pass Rate", "#f59e0b"), ("hostel", "In Hostel", "#ef4444")]
        for col, (key, title, colour) in enumerate(specs):
            top.grid_columnconfigure(col, weight=1)
            card = tk.Frame(top, bg=CARD, highlightthickness=1, highlightbackground="#e5e7eb")
            card.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 10, 0))
            tk.Frame(card, bg=colour, height=5).pack(fill="x")
            var = tk.StringVar(value="0")
            self.vars[key] = var
            tk.Label(card, textvariable=var, font=(FONT, 26, "bold"), bg=CARD,
                     fg=colour).pack(pady=(12, 0))
            tk.Label(card, text=title, bg=CARD, fg=MUTED).pack(pady=(0, 12))

        # --- middle: Canvas chart + Listbox --------------------------------------
        mid = tk.Frame(self, bg=BG)
        mid.pack(fill="both", expand=True, pady=14)
        mid.grid_columnconfigure(0, weight=3)
        mid.grid_columnconfigure(1, weight=2)
        mid.grid_rowconfigure(0, weight=1)

        chart_box = tk.LabelFrame(mid, text=" Students per course ", bg=CARD, fg=TEXT,
                                  font=(FONT, 10, "bold"), padx=8, pady=8)
        chart_box.grid(row=0, column=0, sticky="nsew")
        self.canvas = tk.Canvas(chart_box, bg=CARD, highlightthickness=0, height=240)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_chart())

        right = tk.Frame(mid, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        act_box = tk.LabelFrame(right, text=" Recent activity ", bg=CARD, fg=TEXT,
                                font=(FONT, 10, "bold"), padx=8, pady=8)
        act_box.grid(row=0, column=0, sticky="nsew")
        self.listbox = tk.Listbox(act_box, bd=0, highlightthickness=0, bg=CARD, fg=TEXT,
                                  selectbackground="#c7d2fe", activestyle="none")
        sb = ttk.Scrollbar(act_box, orient="vertical", command=self.listbox.yview)
        self.listbox.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

        # --- bottom: progress bars ----------------------------------------------
        bottom = tk.LabelFrame(self, text=" Overview ", bg=CARD, fg=TEXT,
                               font=(FONT, 10, "bold"), padx=12, pady=8)
        bottom.pack(fill="x")
        bottom.grid_columnconfigure(1, weight=1)
        self.bars = {}
        for r, (key, label) in enumerate([("att", "Average attendance"),
                                          ("pass", "Pass percentage")]):
            tk.Label(bottom, text=label, bg=CARD, width=20, anchor="w").grid(row=r, column=0, pady=4)
            pb = ttk.Progressbar(bottom, orient="horizontal", mode="determinate", maximum=100)
            pb.grid(row=r, column=1, sticky="ew", padx=10)
            val = tk.Label(bottom, text="0%", bg=CARD, width=6)
            val.grid(row=r, column=2)
            self.bars[key] = (pb, val)

    def on_show(self):
        students = self.app.store.students
        n = len(students)
        pm = self.app.pass_mark.get()
        passed = sum(1 for s in students if percentage(s) >= pm)
        avg = sum(percentage(s) for s in students) / n if n else 0
        att = sum(s["attendance"] for s in students) / n if n else 0
        pass_rate = 100 * passed / n if n else 0
        self.vars["total"].set(str(n))
        self.vars["avg"].set(f"{avg:.1f}%")
        self.vars["pass"].set(f"{pass_rate:.0f}%")
        self.vars["hostel"].set(str(sum(1 for s in students if s["hostel"])))
        for key, value in (("att", att), ("pass", pass_rate)):
            pb, lbl = self.bars[key]
            pb["value"] = value
            lbl.config(text=f"{value:.0f}%")
        self.listbox.delete(0, "end")
        for line in self.app.activity or ["No activity yet"]:
            self.listbox.insert("end", line)
        self.draw_chart()

    def draw_chart(self):
        """Hand-drawn bar chart using Canvas primitives."""
        c = self.canvas
        c.delete("all")
        w = max(c.winfo_width(), 400)
        h = max(c.winfo_height(), 200)
        counts = Counter(s["course"] for s in self.app.store.students)
        if not counts:
            c.create_text(w / 2, h / 2, text="No data", fill=MUTED)
            return
        left, bottom, top = 36, h - 38, 24
        peak = max(counts.values())
        slot = (w - left - 20) / len(COURSES)
        c.create_line(left, top, left, bottom, fill="#9ca3af")
        c.create_line(left, bottom, w - 10, bottom, fill="#9ca3af")
        for i in range(0, peak + 1, max(1, peak // 4)):                 # y-axis ticks
            y = bottom - (bottom - top - 14) * i / peak
            c.create_line(left - 4, y, left, y, fill="#9ca3af")
            c.create_text(left - 8, y, text=str(i), anchor="e", fill=MUTED, font=(FONT, 8))
            c.create_line(left, y, w - 10, y, fill="#f3f4f6")
        for i, course in enumerate(COURSES):
            v = counts.get(course, 0)
            x0 = left + i * slot + slot * 0.18
            x1 = x0 + slot * 0.64
            y1 = bottom - (bottom - top - 14) * v / peak
            colour = CHART_COLORS[i % len(CHART_COLORS)]
            rect = c.create_rectangle(x0, y1, x1, bottom, fill=colour, outline="")
            c.create_text((x0 + x1) / 2, y1 - 9, text=str(v), font=(FONT, 9, "bold"), fill=TEXT)
            c.create_text((x0 + x1) / 2, bottom + 16, text=course, font=(FONT, 8),
                          fill=MUTED, width=slot)
            c.tag_bind(rect, "<Enter>", lambda e, r=rect, col=darken(colour, 0.8): c.itemconfig(r, fill=col))
            c.tag_bind(rect, "<Leave>", lambda e, r=rect, col=colour: c.itemconfig(r, fill=col))


# ----------------------------------------------------------------------------
# STUDENTS LIST  (Treeview, Scrollbars, search, filter, context menu)
# ----------------------------------------------------------------------------
class StudentsPage(tk.Frame):
    COLS = [("id", "ID", 50), ("name", "Name", 140), ("age", "Age", 50),
            ("gender", "Gender", 70), ("course", "Course", 100), ("sem", "Sem", 50),
            ("email", "Email", 180), ("phone", "Phone", 100), ("pct", "Marks %", 80)]

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", pady=(0, 10))
        tk.Label(bar, text="Search:", bg=BG).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())   # live search
        app.entry(bar, self.search_var, width=18).pack(side="left", padx=(6, 12), ipady=4)

        tk.Label(bar, text="Course:", bg=BG).pack(side="left")
        self.course_var = tk.StringVar(value="All Courses")
        cb = ttk.Combobox(bar, textvariable=self.course_var, state="readonly", width=12,
                          values=["All Courses"] + COURSES)
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        app.button(bar, "Export CSV", self.export_csv, kind="neutral").pack(side="right")
        app.button(bar, "Delete", self.delete_selected, kind="danger").pack(side="right", padx=6)
        app.button(bar, "Edit", self.edit_selected, kind="warn").pack(side="right")
        app.button(bar, "+ Add", lambda: app.main.new_student(), kind="success").pack(side="right", padx=6)

        wrap = tk.Frame(self, bg=CARD, highlightthickness=1, highlightbackground="#e5e7eb")
        wrap.pack(fill="both", expand=True)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(wrap, columns=[c[0] for c in self.COLS], show="headings",
                                 selectmode="extended")
        for key, title, width in self.COLS:
            self.tree.heading(key, text=title, command=lambda k=key: self.sort_by(k, False))
            self.tree.column(key, width=width, anchor="center" if width < 90 else "w")
        vs = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("odd", background="#f9fafb")
        self.tree.tag_configure("fail", foreground="#dc2626")

        self.count_lbl = tk.Label(self, text="", bg=BG, fg=MUTED, anchor="w")
        self.count_lbl.pack(fill="x", pady=(6, 0))

        # right-click context menu
        self.ctx = tk.Menu(self, tearoff=0)
        self.ctx.add_command(label="Edit student", command=self.edit_selected)
        self.ctx.add_command(label="View report card", command=self.view_report)
        self.ctx.add_separator()
        self.ctx.add_command(label="Delete", command=self.delete_selected)
        for seq in ("<Button-3>", "<Button-2>"):                   # Windows/Linux, macOS
            self.tree.bind(seq, self.popup)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_selected())

    def on_show(self):
        self.refresh()

    def refresh(self):
        q = self.search_var.get().strip().lower()
        course = self.course_var.get()
        pm = self.app.pass_mark.get()
        self.tree.delete(*self.tree.get_children())
        shown = 0
        for s in self.app.store.students:
            if course != "All Courses" and s["course"] != course:
                continue
            if q and q not in s["name"].lower() and q not in s["email"].lower() and q != str(s["id"]):
                continue
            pct = percentage(s)
            tags = ["odd"] if shown % 2 else []
            if pct < pm:
                tags.append("fail")
            self.tree.insert("", "end", iid=str(s["id"]), tags=tags,
                             values=(s["id"], s["name"], s["age"], s["gender"], s["course"],
                                     s["semester"], s["email"], s["phone"], f"{pct:.1f}%"))
            shown += 1
        self.count_lbl.config(text=f"Showing {shown} of {len(self.app.store.students)} students"
                                   "   •   red rows = below pass mark   •   click a heading to sort"
                                   "   •   right-click for more")

    def sort_by(self, col, reverse):
        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            rows.sort(key=lambda t: float(t[0].rstrip("%")), reverse=reverse)
        except ValueError:
            rows.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for i, (_, k) in enumerate(rows):
            self.tree.move(k, "", i)
            tags = [t for t in self.tree.item(k, "tags") if t != "odd"]
            if i % 2:
                tags.append("odd")
            self.tree.item(k, tags=tags)
        self.tree.heading(col, command=lambda: self.sort_by(col, not reverse))

    def popup(self, event):
        row = self.tree.identify_row(event.y)
        if row:
            if row not in self.tree.selection():
                self.tree.selection_set(row)
            self.ctx.tk_popup(event.x_root, event.y_root)

    def selected_ids(self):
        return [int(i) for i in self.tree.selection()]

    def edit_selected(self):
        ids = self.selected_ids()
        if not ids:
            messagebox.showwarning("No selection", "Please select a student first.")
            return
        self.app.main.pages["form"].load(ids[0])
        self.app.main.show_page("form")

    def view_report(self):
        ids = self.selected_ids()
        if ids:
            marks = self.app.main.pages["marks"]
            marks.select_student(ids[0])
            self.app.main.show_page("marks")
            marks.notebook.select(1)

    def delete_selected(self):
        ids = self.selected_ids()
        if not ids:
            messagebox.showwarning("No selection", "Please select at least one student.")
            return
        if self.app.confirm_delete.get() and not messagebox.askyesno(
                "Confirm delete", f"Delete {len(ids)} selected student(s)? This cannot be undone.",
                icon="warning"):
            return
        for sid in ids:
            self.app.store.delete(sid)
        self.app.log(f"Deleted {len(ids)} student(s)")
        self.app.set_status(f"Deleted {len(ids)} student(s)")
        self.refresh()

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", initialfile="students.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID", "Name", "Age", "Gender", "Email", "Phone", "Course", "Semester",
                        "Scholarship", "Hostel", "Attendance"] + SUBJECTS + ["Percentage", "Grade"])
            for s in self.app.store.students:
                p = percentage(s)
                w.writerow([s["id"], s["name"], s["age"], s["gender"], s["email"], s["phone"],
                            s["course"], s["semester"], s["scholarship"], s["hostel"],
                            s["attendance"]] + [s["marks"].get(x, 0) for x in SUBJECTS]
                           + [f"{p:.1f}", grade_for(p)])
        self.app.log("Exported students to CSV")
        messagebox.showinfo("Export complete", f"Saved to:\n{path}")


# ----------------------------------------------------------------------------
# ADD / EDIT FORM  (Entry, Spinbox, Radiobutton, Combobox, Scale, OptionMenu,
#                   Listbox, Checkbutton, Text, validation)
# ----------------------------------------------------------------------------
class StudentFormPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.editing_id = None

        self.heading = tk.Label(self, text="Add New Student", font=(FONT, 14, "bold"),
                                bg=BG, fg=TEXT)
        self.heading.pack(anchor="w", pady=(0, 8))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1, uniform="col")
        body.grid_columnconfigure(1, weight=1, uniform="col")

        # ---------------- left card: personal information ----------------
        p = tk.LabelFrame(body, text=" Personal information ", bg=CARD, fg=TEXT,
                          font=(FONT, 10, "bold"), padx=16, pady=12)
        p.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        p.grid_columnconfigure(1, weight=1)

        self.name_var, self.email_var, self.phone_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.age_var = tk.IntVar(value=18)
        self.gender_var = tk.StringVar(value="Male")

        def lbl(text, row):
            tk.Label(p, text=text, bg=CARD, anchor="w").grid(row=row, column=0, sticky="w", pady=7)

        lbl("Full name *", 0)
        app.entry(p, self.name_var).grid(row=0, column=1, sticky="ew", ipady=4)

        lbl("Age", 1)
        tk.Spinbox(p, from_=16, to=40, textvariable=self.age_var, width=6, relief="flat",
                   highlightthickness=1, highlightbackground="#d1d5db").grid(
            row=1, column=1, sticky="w", ipady=3)

        lbl("Gender", 2)
        gframe = tk.Frame(p, bg=CARD)
        gframe.grid(row=2, column=1, sticky="w")
        for g in ("Male", "Female", "Other"):
            tk.Radiobutton(gframe, text=g, variable=self.gender_var, value=g, bg=CARD,
                           activebackground=CARD, cursor="hand2").pack(side="left", padx=(0, 10))

        lbl("Email *", 3)
        app.entry(p, self.email_var).grid(row=3, column=1, sticky="ew", ipady=4)

        lbl("Phone *", 4)
        vcmd = (self.register(self._digits_only), "%P")       # validate every keystroke
        app.entry(p, self.phone_var, validate="key", validatecommand=vcmd).grid(
            row=4, column=1, sticky="ew", ipady=4)
        tk.Label(p, text="10 digits (letters are blocked)", fg=MUTED, bg=CARD,
                 font=(FONT, 8)).grid(row=5, column=1, sticky="w")

        lbl("Address", 6)
        addr_frame = tk.Frame(p, bg=CARD)
        addr_frame.grid(row=6, column=1, sticky="ew")
        self.address = tk.Text(addr_frame, height=4, width=30, wrap="word", relief="flat",
                               highlightthickness=1, highlightbackground="#d1d5db",
                               font=(FONT, 10), bg="#f9fafb")
        asb = ttk.Scrollbar(addr_frame, command=self.address.yview)
        self.address.config(yscrollcommand=asb.set)
        self.address.pack(side="left", fill="both", expand=True)
        asb.pack(side="right", fill="y")

        # ---------------- right card: academic information ----------------
        a = tk.LabelFrame(body, text=" Academic information ", bg=CARD, fg=TEXT,
                          font=(FONT, 10, "bold"), padx=16, pady=12)
        a.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        a.grid_columnconfigure(1, weight=1)

        self.course_var = tk.StringVar(value=COURSES[0])
        self.sem_var = tk.IntVar(value=1)
        self.scholar_var = tk.StringVar(value=SCHOLARSHIPS[0])
        self.hostel_var = tk.BooleanVar(value=False)

        def alb(text, row):
            tk.Label(a, text=text, bg=CARD, anchor="w").grid(row=row, column=0, sticky="nw", pady=7)

        alb("Course", 0)
        ttk.Combobox(a, textvariable=self.course_var, values=COURSES, state="readonly").grid(
            row=0, column=1, sticky="ew")

        alb("Semester", 1)
        tk.Scale(a, from_=1, to=8, orient="horizontal", variable=self.sem_var, tickinterval=1,
                 bg=CARD, highlightthickness=0, troughcolor="#e5e7eb", length=240,
                 cursor="sb_h_double_arrow").grid(row=1, column=1, sticky="w")

        alb("Scholarship", 2)
        om = tk.OptionMenu(a, self.scholar_var, *SCHOLARSHIPS)
        om.config(bg="#f9fafb", relief="flat", highlightthickness=1,
                  highlightbackground="#d1d5db", width=14, anchor="w")
        om.grid(row=2, column=1, sticky="w")

        alb("Skills\n(Ctrl+click for\nmultiple)", 3)
        sk = tk.Frame(a, bg=CARD)
        sk.grid(row=3, column=1, sticky="ew")
        self.skills = tk.Listbox(sk, selectmode="multiple", height=6, exportselection=False,
                                 relief="flat", highlightthickness=1,
                                 highlightbackground="#d1d5db", selectbackground="#c7d2fe",
                                 selectforeground="black", activestyle="none")
        for s in SKILLS:
            self.skills.insert("end", s)
        ssb = ttk.Scrollbar(sk, command=self.skills.yview)
        self.skills.config(yscrollcommand=ssb.set)
        self.skills.pack(side="left", fill="both", expand=True)
        ssb.pack(side="right", fill="y")

        tk.Checkbutton(a, text="Needs hostel accommodation", variable=self.hostel_var,
                       bg=CARD, activebackground=CARD, cursor="hand2").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # ---------------- buttons ----------------
        btns = tk.Frame(self, bg=BG)
        btns.pack(fill="x", pady=12)
        app.button(btns, "💾  Save", self.save, kind="success").pack(side="left")
        app.button(btns, "Clear", lambda: self.load(self.editing_id), kind="neutral").pack(
            side="left", padx=8)
        app.button(btns, "Cancel", lambda: app.main.show_page("students"),
                   kind="danger").pack(side="left")

    @staticmethod
    def _digits_only(proposed):
        return proposed == "" or (proposed.isdigit() and len(proposed) <= 10)

    def on_show(self):
        pass

    # --------- fill the form (blank for new, or existing student) ---------
    def load(self, sid):
        self.editing_id = sid
        s = self.app.store.get(sid) if sid else None
        self.heading.config(text=f"Edit Student #{sid}" if s else "Add New Student")
        self.name_var.set(s["name"] if s else "")
        self.age_var.set(s["age"] if s else 18)
        self.gender_var.set(s["gender"] if s else "Male")
        self.email_var.set(s["email"] if s else "")
        self.phone_var.set(s["phone"] if s else "")
        self.address.delete("1.0", "end")
        self.address.insert("1.0", s["address"] if s else "")
        self.course_var.set(s["course"] if s else COURSES[0])
        self.sem_var.set(s["semester"] if s else 1)
        self.scholar_var.set(s["scholarship"] if s else SCHOLARSHIPS[0])
        self.hostel_var.set(s["hostel"] if s else False)
        self.skills.selection_clear(0, "end")
        for i, name in enumerate(SKILLS):
            if s and name in s["skills"]:
                self.skills.selection_set(i)

    def save(self):
        name, email, phone = self.name_var.get().strip(), self.email_var.get().strip(), self.phone_var.get()
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,}", name):
            return messagebox.showerror("Invalid name", "Enter a valid name (letters only).")
        if not re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.-]+", email):
            return messagebox.showerror("Invalid email", "Enter a valid email address.")
        if len(phone) != 10:
            return messagebox.showerror("Invalid phone", "Phone number must have exactly 10 digits.")
        try:
            age = int(self.age_var.get())
        except (tk.TclError, ValueError):
            return messagebox.showerror("Invalid age", "Age must be a number.")

        old = self.app.store.get(self.editing_id) if self.editing_id else None
        student = {
            "id": self.editing_id or self.app.store.next_id(), "name": name, "age": age,
            "gender": self.gender_var.get(), "email": email, "phone": phone,
            "course": self.course_var.get(), "semester": self.sem_var.get(),
            "scholarship": self.scholar_var.get(),
            "skills": [self.skills.get(i) for i in self.skills.curselection()],
            "hostel": self.hostel_var.get(),
            "address": self.address.get("1.0", "end-1c").strip(),
            "marks": old["marks"] if old else {s: 0 for s in SUBJECTS},
            "attendance": old["attendance"] if old else 75,
        }
        if old:
            self.app.store.update(student)
            self.app.log(f"Updated {name}")
            self.app.set_status(f"Updated {name}")
        else:
            self.app.store.add(student)
            self.app.log(f"Added {name}")
            self.app.set_status(f"Added {name}")
        messagebox.showinfo("Saved", f"{name} saved successfully.")
        self.load(None)
        self.app.main.show_page("students")


# ----------------------------------------------------------------------------
# MARKS & REPORTS  (Notebook tabs, Scale, Text with tags, Treeview ranking)
# ----------------------------------------------------------------------------
class MarksPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app

        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", pady=(0, 10))
        tk.Label(top, text="Select student:", bg=BG, font=(FONT, 10, "bold")).pack(side="left")
        self.student_var = tk.StringVar()
        self.combo = ttk.Combobox(top, textvariable=self.student_var, state="readonly", width=34)
        self.combo.pack(side="left", padx=8)
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.load_marks())

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self.tab_marks = tk.Frame(self.notebook, bg=CARD, padx=20, pady=14)
        self.tab_report = tk.Frame(self.notebook, bg=CARD, padx=14, pady=14)
        self.tab_rank = tk.Frame(self.notebook, bg=CARD, padx=14, pady=14)
        self.notebook.add(self.tab_marks, text="  Enter Marks  ")
        self.notebook.add(self.tab_report, text="  Report Card  ")
        self.notebook.add(self.tab_rank, text="  Class Ranking  ")
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab)

        # ---- tab 1 : sliders for each subject ----
        self.mark_vars = {s: tk.IntVar(value=0) for s in SUBJECTS}
        self.tab_marks.grid_columnconfigure(1, weight=1)
        for r, subj in enumerate(SUBJECTS):
            tk.Label(self.tab_marks, text=subj, bg=CARD, width=14, anchor="w",
                     font=(FONT, 10, "bold")).grid(row=r, column=0, pady=8)
            tk.Scale(self.tab_marks, from_=0, to=100, orient="horizontal", variable=self.mark_vars[subj],
                     bg=CARD, highlightthickness=0, troughcolor="#e5e7eb", tickinterval=25,
                     command=lambda v: self.update_preview()).grid(row=r, column=1, sticky="ew", padx=10)
            tk.Spinbox(self.tab_marks, from_=0, to=100, width=5, textvariable=self.mark_vars[subj],
                       command=self.update_preview).grid(row=r, column=2)

        r = len(SUBJECTS)
        tk.Label(self.tab_marks, text="Attendance %", bg=CARD, width=14, anchor="w",
                 font=(FONT, 10, "bold")).grid(row=r, column=0, pady=8)
        self.att_var = tk.IntVar(value=75)
        tk.Scale(self.tab_marks, from_=0, to=100, orient="horizontal", variable=self.att_var,
                 bg=CARD, highlightthickness=0, troughcolor="#e5e7eb", tickinterval=25).grid(
            row=r, column=1, sticky="ew", padx=10)

        self.preview = tk.Label(self.tab_marks, text="", bg=CARD, font=(FONT, 12, "bold"), fg=TEXT)
        self.preview.grid(row=r + 1, column=0, columnspan=3, pady=(14, 4))
        self.pbar = ttk.Progressbar(self.tab_marks, maximum=100, mode="determinate")
        self.pbar.grid(row=r + 2, column=0, columnspan=3, sticky="ew")
        app.button(self.tab_marks, "💾  Save marks", self.save_marks, kind="success").grid(
            row=r + 3, column=0, columnspan=3, pady=16)

        # ---- tab 2 : report card in a Text widget with formatting tags ----
        self.report = tk.Text(self.tab_report, wrap="word", state="disabled", relief="flat",
                              font=("Courier New", 11), padx=16, pady=12, bg="#fafafa")
        self.report.pack(fill="both", expand=True)
        self.report.tag_configure("title", font=(FONT, 16, "bold"), justify="center", foreground=app.accent)
        self.report.tag_configure("bold", font=("Courier New", 11, "bold"))
        self.report.tag_configure("pass", foreground="#059669", font=("Courier New", 12, "bold"))
        self.report.tag_configure("fail", foreground="#dc2626", font=("Courier New", 12, "bold"))
        self.report.tag_configure("muted", foreground=MUTED)
        rb = tk.Frame(self.tab_report, bg=CARD)
        rb.pack(fill="x", pady=(8, 0))
        app.button(rb, "Copy to clipboard", self.copy_report, kind="neutral").pack(side="left")

        # ---- tab 3 : ranking table ----
        cols = ("rank", "name", "course", "total", "pct", "grade", "result")
        self.rank_tree = ttk.Treeview(self.tab_rank, columns=cols, show="headings")
        for c, t, w in [("rank", "Rank", 50), ("name", "Name", 180), ("course", "Course", 120),
                        ("total", "Total", 70), ("pct", "Percentage", 90),
                        ("grade", "Grade", 60), ("result", "Result", 80)]:
            self.rank_tree.heading(c, text=t)
            self.rank_tree.column(c, width=w, anchor="center" if c != "name" else "w")
        self.rank_tree.pack(fill="both", expand=True)
        self.rank_tree.tag_configure("gold", background="#fef3c7")
        self.rank_tree.tag_configure("fail", foreground="#dc2626")

    # ---------- helpers ----------
    def student_list(self):
        return [f"{s['id']} - {s['name']}" for s in self.app.store.students]

    def on_show(self):
        self.combo["values"] = self.student_list()
        if not self.student_var.get() and self.combo["values"]:
            self.combo.current(0)
        self.load_marks()
        self.fill_ranking()

    def select_student(self, sid):
        self.combo["values"] = self.student_list()
        for i, v in enumerate(self.combo["values"]):
            if v.startswith(f"{sid} -"):
                self.combo.current(i)
        self.load_marks()

    def current_student(self):
        text = self.student_var.get()
        return self.app.store.get(int(text.split(" - ")[0])) if text else None

    def load_marks(self):
        s = self.current_student()
        if not s:
            return
        for subj in SUBJECTS:
            self.mark_vars[subj].set(s["marks"].get(subj, 0))
        self.att_var.set(s["attendance"])
        self.update_preview()
        self.build_report()

    def update_preview(self):
        try:
            total = sum(v.get() for v in self.mark_vars.values())
        except tk.TclError:
            return
        pct = total / len(SUBJECTS)
        self.pbar["value"] = pct
        self.preview.config(text=f"Total {total}/{100 * len(SUBJECTS)}   •   {pct:.1f}%   •   Grade {grade_for(pct)}",
                            fg="#059669" if pct >= self.app.pass_mark.get() else "#dc2626")

    def save_marks(self):
        s = self.current_student()
        if not s:
            return messagebox.showwarning("No student", "Select a student first.")
        s["marks"] = {k: int(v.get()) for k, v in self.mark_vars.items()}
        s["attendance"] = self.att_var.get()
        self.app.store.update(s)
        self.app.log(f"Marks updated for {s['name']}")
        self.app.set_status(f"Marks saved for {s['name']}")
        self.build_report()
        self.fill_ranking()

    def build_report(self):
        s = self.current_student()
        t = self.report
        t.config(state="normal")
        t.delete("1.0", "end")
        if s:
            pct = percentage(s)
            passed = pct >= self.app.pass_mark.get()
            t.insert("end", "REPORT CARD\n\n", "title")
            t.insert("end", f"Name       : ", "bold"); t.insert("end", f"{s['name']}\n")
            t.insert("end", f"Student ID : ", "bold"); t.insert("end", f"{s['id']}\n")
            t.insert("end", f"Course     : ", "bold"); t.insert("end", f"{s['course']}  (Semester {s['semester']})\n")
            t.insert("end", f"Attendance : ", "bold"); t.insert("end", f"{s['attendance']}%\n")
            t.insert("end", "\n" + "-" * 44 + "\n", "muted")
            t.insert("end", f"{'Subject':<20}{'Marks':>8}{'Out of':>10}\n", "bold")
            t.insert("end", "-" * 44 + "\n", "muted")
            for subj in SUBJECTS:
                t.insert("end", f"{subj:<20}{s['marks'].get(subj, 0):>8}{100:>10}\n")
            t.insert("end", "-" * 44 + "\n", "muted")
            t.insert("end", f"{'Percentage':<20}{pct:>7.1f}%\n", "bold")
            t.insert("end", f"{'Grade':<20}{grade_for(pct):>8}\n\n", "bold")
            t.insert("end", "RESULT: PASS\n" if passed else "RESULT: FAIL\n", "pass" if passed else "fail")
        t.config(state="disabled")

    def copy_report(self):
        self.clipboard_clear()
        self.clipboard_append(self.report.get("1.0", "end-1c"))
        self.app.set_status("Report card copied to clipboard")

    def fill_ranking(self):
        self.rank_tree.delete(*self.rank_tree.get_children())
        ranked = sorted(self.app.store.students, key=percentage, reverse=True)
        pm = self.app.pass_mark.get()
        for i, s in enumerate(ranked, start=1):
            pct = percentage(s)
            tags = []
            if i <= 3:
                tags.append("gold")
            if pct < pm:
                tags.append("fail")
            self.rank_tree.insert("", "end", tags=tags, values=(
                i, s["name"], s["course"], sum(s["marks"].values()), f"{pct:.1f}%",
                grade_for(pct), "Pass" if pct >= pm else "Fail"))

    def on_tab(self, _event):
        if self.notebook.index("current") == 1:
            self.build_report()


# ----------------------------------------------------------------------------
# WIDGET LAB : a tour of Tkinter properties (relief, fonts, cursors, images,
#              pack/grid/place, Menubutton, Message, PanedWindow, events, dialogs)
# ----------------------------------------------------------------------------
class WidgetLabPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        for builder, title in [(self.tab_appearance, "  Appearance  "),
                               (self.tab_geometry, "  Geometry Managers  "),
                               (self.tab_inputs, "  Input Widgets  "),
                               (self.tab_events, "  Events & Dialogs  ")]:
            f = tk.Frame(nb, bg=CARD, padx=16, pady=12)
            nb.add(f, text=title)
            builder(f)

    # ------------------------------------------------------------ appearance
    def tab_appearance(self, f):
        tk.Label(f, text="relief = border style (with bd=borderwidth)", bg=CARD, fg=MUTED).pack(anchor="w")
        row = tk.Frame(f, bg=CARD)
        row.pack(fill="x", pady=6)
        for relief in ("flat", "raised", "sunken", "groove", "ridge", "solid"):
            tk.Label(row, text=relief, relief=relief, bd=3, width=11, height=2,
                     bg="#f3f4f6").pack(side="left", padx=5)

        tk.Label(f, text="fonts: family, size, weight, slant, underline, overstrike",
                 bg=CARD, fg=MUTED).pack(anchor="w", pady=(14, 0))
        row = tk.Frame(f, bg=CARD)
        row.pack(fill="x", pady=6)
        for text, font in [("Bold", (FONT, 12, "bold")), ("Italic", (FONT, 12, "italic")),
                           ("Underline", (FONT, 12, "underline")),
                           ("Strike", (FONT, 12, "overstrike")),
                           ("Courier", ("Courier New", 12)), ("Large", (FONT, 20, "bold"))]:
            tk.Label(row, text=text, font=font, bg=CARD).pack(side="left", padx=10)

        tk.Label(f, text="colours: fg, bg, activebackground, highlightbackground (names or #hex)",
                 bg=CARD, fg=MUTED).pack(anchor="w", pady=(14, 0))
        row = tk.Frame(f, bg=CARD)
        row.pack(fill="x", pady=6)
        for bg, fg in [("tomato", "white"), ("#10b981", "white"), ("gold", "black"),
                       ("navy", "yellow"), ("lavender", "purple")]:
            tk.Button(row, text=bg, bg=bg, fg=fg, relief="flat", padx=12, pady=5,
                      activebackground="black", activeforeground="white").pack(side="left", padx=5)

        tk.Label(f, text="cursor = mouse pointer shape when hovering (move the mouse over each)",
                 bg=CARD, fg=MUTED).pack(anchor="w", pady=(14, 0))
        row = tk.Frame(f, bg=CARD)
        row.pack(fill="x", pady=6)
        for cur in ("hand2", "watch", "cross", "plus", "question_arrow", "xterm", "circle"):
            tk.Label(row, text=cur, cursor=cur, bg="#e0e7ff", padx=10, pady=8).pack(side="left", padx=4)

        tk.Label(f, text="text layout: anchor, justify, wraplength, padx/pady; images with PhotoImage",
                 bg=CARD, fg=MUTED).pack(anchor="w", pady=(14, 0))
        row = tk.Frame(f, bg=CARD)
        row.pack(fill="x", pady=6)
        tk.Label(row, text="Wrapped, centred text that is justified across several lines",
                 wraplength=160, justify="center", anchor="n", bg="#fef9c3", width=22,
                 height=4, bd=2, relief="groove").pack(side="left", padx=5)
        # a gradient image generated in code (no external file needed)
        self.img = tk.PhotoImage(width=120, height=60)
        for x in range(120):
            colour = "#%02x%02x%02x" % (int(70 + x), 90, int(255 - x))
            self.img.put(colour, to=(x, 0, x + 1, 60))
        tk.Label(row, image=self.img, bd=2, relief="ridge").pack(side="left", padx=10)
        tk.Label(row, image=self.img, text="Text over image", compound="center",
                 fg="white", font=(FONT, 11, "bold")).pack(side="left", padx=5)

    # ------------------------------------------------------------ geometry
    def tab_geometry(self, f):
        f.grid_columnconfigure((0, 1, 2), weight=1, uniform="g")
        f.grid_rowconfigure(0, weight=1)

        box = tk.LabelFrame(f, text=" pack() ", bg=CARD, padx=8, pady=8)
        box.grid(row=0, column=0, sticky="nsew", padx=5)
        tk.Label(box, text="side / fill / expand / padx / anchor", bg=CARD, fg=MUTED,
                 font=(FONT, 8)).pack()
        tk.Button(box, text="side=TOP, fill=X", bg="#c7d2fe").pack(side="top", fill="x", pady=3)
        mid = tk.Frame(box, bg=CARD)
        mid.pack(fill="both", expand=True)
        tk.Button(mid, text="LEFT", bg="#fde68a").pack(side="left", fill="y", padx=3)
        tk.Button(mid, text="expand=True\nfill=BOTH", bg="#a7f3d0").pack(side="left", fill="both", expand=True)
        tk.Button(mid, text="RIGHT", bg="#fecaca").pack(side="right", fill="y", padx=3)
        tk.Button(box, text="side=BOTTOM, anchor=E", bg="#ddd6fe").pack(side="bottom", anchor="e", pady=3)

        box = tk.LabelFrame(f, text=" grid() ", bg=CARD, padx=8, pady=8)
        box.grid(row=0, column=1, sticky="nsew", padx=5)
        box.grid_columnconfigure((0, 1, 2), weight=1)
        box.grid_rowconfigure((0, 1, 2), weight=1)
        tk.Button(box, text="row0 col0\ncolumnspan=2", bg="#c7d2fe").grid(row=0, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)
        tk.Button(box, text="r0 c2", bg="#fde68a").grid(row=0, column=2, sticky="nsew", padx=2, pady=2)
        tk.Button(box, text="rowspan=2", bg="#a7f3d0").grid(row=1, column=0, rowspan=2, sticky="nsew", padx=2, pady=2)
        tk.Button(box, text="sticky=EW", bg="#fecaca").grid(row=1, column=1, columnspan=2, sticky="ew", padx=2, pady=2)
        tk.Button(box, text="sticky=NSEW", bg="#ddd6fe").grid(row=2, column=1, columnspan=2, sticky="nsew", padx=2, pady=2)

        box = tk.LabelFrame(f, text=" place() ", bg=CARD, padx=8, pady=8)
        box.grid(row=0, column=2, sticky="nsew", padx=5)
        area = tk.Frame(box, bg="#f3f4f6", relief="sunken", bd=2)
        area.pack(fill="both", expand=True)
        tk.Label(area, text="x=10, y=10", bg="#c7d2fe").place(x=10, y=10)
        tk.Label(area, text="relx=.5 rely=.5\nanchor=CENTER", bg="#a7f3d0").place(relx=.5, rely=.5, anchor="center")
        tk.Label(area, text="relx=1 rely=1 anchor=SE", bg="#fecaca").place(relx=1, rely=1, anchor="se", x=-4, y=-4)
        tk.Label(area, text="relwidth=.9", bg="#fde68a").place(relx=.05, rely=.8, relwidth=.9, height=22)

    # ------------------------------------------------------------ inputs
    def tab_inputs(self, f):
        for c in range(3):
            f.grid_columnconfigure(c, weight=1, uniform="i")

        # column 0
        c0 = tk.LabelFrame(f, text=" Entry / Spinbox / Combobox ", bg=CARD, padx=8, pady=6)
        c0.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.e_var = tk.StringVar(value="secret")
        tk.Entry(c0, textvariable=self.e_var, show="*", justify="center").pack(fill="x", pady=3)
        tk.Label(c0, text="↑ Entry with show='*', justify='center'", bg=CARD, fg=MUTED, font=(FONT, 8)).pack()
        tk.Spinbox(c0, values=("Mon", "Tue", "Wed", "Thu", "Fri"), wrap=True).pack(fill="x", pady=3)
        tk.Label(c0, text="↑ Spinbox with values & wrap", bg=CARD, fg=MUTED, font=(FONT, 8)).pack()
        ttk.Combobox(c0, values=["Python", "Java", "C++"], state="readonly").pack(fill="x", pady=3)
        tk.Label(c0, text="↑ ttk.Combobox (readonly)", bg=CARD, fg=MUTED, font=(FONT, 8)).pack()
        tk.Message(c0, text="Message widget: auto-wraps long text to a fixed width.",
                   width=170, bg="#fef9c3").pack(pady=6)

        # column 1
        c1 = tk.LabelFrame(f, text=" Check / Radio / Scale ", bg=CARD, padx=8, pady=6)
        c1.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self.c1, self.c2 = tk.BooleanVar(value=True), tk.BooleanVar()
        tk.Checkbutton(c1, text="Checkbutton A", variable=self.c1, bg=CARD).pack(anchor="w")
        tk.Checkbutton(c1, text="Checkbutton B", variable=self.c2, bg=CARD).pack(anchor="w")
        self.r = tk.StringVar(value="b")
        for v in "abc":
            tk.Radiobutton(c1, text=f"Radiobutton {v.upper()}", variable=self.r, value=v, bg=CARD).pack(anchor="w")
        tk.Radiobutton(c1, text="Indicator off (button style)", variable=self.r, value="d",
                       indicatoron=False, bg="#e0e7ff", selectcolor="#a5b4fc").pack(fill="x", pady=4)
        sc = tk.Scale(c1, from_=0, to=100, orient="horizontal", resolution=5, tickinterval=50, bg=CARD,
                      highlightthickness=0, label="Scale (resolution=5)")
        sc.pack(fill="x")
        mb = tk.Menubutton(c1, text="Menubutton ▾", relief="raised", bg="#e0e7ff")
        menu = tk.Menu(mb, tearoff=0)
        self.mb_var = tk.StringVar(value="Medium")
        for opt in ("Low", "Medium", "High"):
            menu.add_radiobutton(label=opt, variable=self.mb_var, value=opt)
        mb.config(menu=menu)
        mb.pack(anchor="w", pady=6)
        tk.Label(c1, textvariable=self.mb_var, bg=CARD, fg=MUTED).pack(anchor="w")

        # column 2
        c2 = tk.LabelFrame(f, text=" Listbox / PanedWindow / Progressbar ", bg=CARD, padx=8, pady=6)
        c2.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)
        pw = tk.PanedWindow(c2, orient="horizontal", sashrelief="raised", sashwidth=6, height=110)
        pw.pack(fill="x")
        lb1 = tk.Listbox(pw, selectmode="browse", exportselection=False)
        lb2 = tk.Listbox(pw, selectmode="extended", exportselection=False)
        for i in range(1, 8):
            lb1.insert("end", f"Browse {i}")
            lb2.insert("end", f"Extended {i}")
        pw.add(lb1)
        pw.add(lb2)
        tk.Label(c2, text="↑ PanedWindow: drag the divider", bg=CARD, fg=MUTED, font=(FONT, 8)).pack()
        self.indet = ttk.Progressbar(c2, mode="indeterminate")
        self.indet.pack(fill="x", pady=(10, 4))
        row = tk.Frame(c2, bg=CARD)
        row.pack()
        tk.Button(row, text="Start", command=lambda: self.indet.start(12)).pack(side="left", padx=2)
        tk.Button(row, text="Stop", command=self.indet.stop).pack(side="left", padx=2)
        ttk.Separator(c2, orient="horizontal").pack(fill="x", pady=10)
        tk.Button(c2, text="state=DISABLED", state="disabled").pack(anchor="w")
        tk.Label(c2, text="↑ disabled widget", bg=CARD, fg=MUTED, font=(FONT, 8)).pack(anchor="w")

    # ------------------------------------------------------------ events
    def tab_events(self, f):
        f.grid_columnconfigure(0, weight=1)
        f.grid_columnconfigure(1, weight=1)

        ev = tk.LabelFrame(f, text=" Event binding: bind() ", bg=CARD, padx=10, pady=8)
        ev.grid(row=0, column=0, sticky="nsew", padx=5)
        self.pad = tk.Label(ev, text="Move / click / double-click / scroll here", bg="#e0e7ff",
                            height=5, relief="sunken", cursor="crosshair")
        self.pad.pack(fill="x")
        self.ev_text = tk.StringVar(value="Waiting for an event…")
        tk.Label(ev, textvariable=self.ev_text, bg=CARD, fg="#4338ca", justify="left").pack(anchor="w", pady=6)
        self.pad.bind("<Motion>", lambda e: self.ev_text.set(f"<Motion>  x={e.x}  y={e.y}"))
        self.pad.bind("<Button-1>", lambda e: self.ev_text.set(f"<Button-1>  left click at ({e.x},{e.y})"))
        self.pad.bind("<Double-Button-1>", lambda e: self.ev_text.set("<Double-Button-1>  double click!"))
        self.pad.bind("<MouseWheel>", lambda e: self.ev_text.set(f"<MouseWheel>  delta={e.delta}"))
        self.pad.bind("<Enter>", lambda e: self.pad.config(bg="#c7d2fe"))
        self.pad.bind("<Leave>", lambda e: self.pad.config(bg="#e0e7ff"))
        tk.Label(ev, text="Type in the box below (<KeyPress>):", bg=CARD).pack(anchor="w")
        ke = tk.Entry(ev)
        ke.pack(fill="x")
        ke.bind("<KeyPress>", lambda e: self.ev_text.set(f"<KeyPress>  keysym={e.keysym}  char={e.char!r}"))
        ke.bind("<Control-a>", lambda e: (ke.select_range(0, "end"), "break")[1])
        ke.bind("<FocusIn>", lambda e: ke.config(bg="#fef9c3"))
        ke.bind("<FocusOut>", lambda e: ke.config(bg="white"))

        dl = tk.LabelFrame(f, text=" Standard dialogs ", bg=CARD, padx=10, pady=8)
        dl.grid(row=0, column=1, sticky="nsew", padx=5)
        dl.grid_columnconfigure((0, 1), weight=1)
        self.dlg_result = tk.StringVar(value="Result will appear here")
        tests = [
            ("showinfo", lambda: messagebox.showinfo("Info", "This is an information box.")),
            ("showwarning", lambda: messagebox.showwarning("Warning", "This is a warning box.")),
            ("showerror", lambda: messagebox.showerror("Error", "This is an error box.")),
            ("askyesno", lambda: self.dlg_result.set(f"askyesno → {messagebox.askyesno('Question', 'Do you like Tkinter?')}")),
            ("askokcancel", lambda: self.dlg_result.set(f"askokcancel → {messagebox.askokcancel('Confirm', 'Proceed?')}")),
            ("askretrycancel", lambda: self.dlg_result.set(f"askretrycancel → {messagebox.askretrycancel('Retry', 'Try again?')}")),
            ("askstring", lambda: self.dlg_result.set(f"askstring → {simpledialog.askstring('Input', 'Your name?')}")),
            ("askinteger", lambda: self.dlg_result.set(f"askinteger → {simpledialog.askinteger('Input', 'Your age?', minvalue=1, maxvalue=100)}")),
            ("askopenfilename", lambda: self.dlg_result.set(f"file → {filedialog.askopenfilename() or 'cancelled'}")),
            ("askcolor", lambda: self.dlg_result.set(f"colour → {colorchooser.askcolor()[1]}")),
            ("Toplevel window", self.open_toplevel),
        ]
        for i, (txt, cmd) in enumerate(tests):
            tk.Button(dl, text=txt, command=cmd, bg="#f3f4f6", relief="groove").grid(
                row=i // 2, column=i % 2, sticky="ew", padx=3, pady=3)
        tk.Label(dl, textvariable=self.dlg_result, bg=CARD, fg="#4338ca", wraplength=300,
                 justify="left").grid(row=7, column=0, columnspan=2, pady=8, sticky="w")

    def open_toplevel(self):
        win = tk.Toplevel(self)                    # a second window
        win.title("Toplevel window")
        win.geometry("300x160+300+250")
        win.resizable(False, False)
        win.transient(self.winfo_toplevel())       # stay on top of the main window
        win.grab_set()                             # modal: block the main window
        tk.Label(win, text="I am a Toplevel window", font=(FONT, 13, "bold")).pack(pady=24)
        tk.Button(win, text="Close", command=win.destroy).pack()


# ----------------------------------------------------------------------------
# SETTINGS  (colorchooser, Radiobutton presets, Scale, Spinbox, data tools)
# ----------------------------------------------------------------------------
class SettingsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self.grid_columnconfigure((0, 1), weight=1, uniform="s")

        # --- appearance ---
        ap = tk.LabelFrame(self, text=" Appearance ", bg=CARD, font=(FONT, 10, "bold"), padx=16, pady=12)
        ap.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))
        tk.Label(ap, text="Accent colour preset", bg=CARD).pack(anchor="w")
        self.preset = tk.StringVar(value="Indigo")
        for name, colour in ACCENT_PRESETS.items():
            row = tk.Frame(ap, bg=CARD)
            row.pack(anchor="w", pady=2)
            tk.Frame(row, bg=colour, width=18, height=18).pack(side="left", padx=(0, 8))
            tk.Radiobutton(row, text=name, variable=self.preset, value=name, bg=CARD,
                           activebackground=CARD, command=lambda c=colour: app.apply_accent(c)).pack(side="left")
        app.button(ap, "Pick custom colour…", self.pick_colour, kind="neutral").pack(anchor="w", pady=(10, 4))

        tk.Label(ap, text="Base font size", bg=CARD).pack(anchor="w", pady=(10, 0))
        self.size = tk.IntVar(value=10)
        tk.Scale(ap, from_=8, to=16, orient="horizontal", variable=self.size, bg=CARD,
                 highlightthickness=0, troughcolor="#e5e7eb", command=self.change_font).pack(fill="x")
        tk.Label(ap, text="(affects widgets that use the default font)", bg=CARD, fg=MUTED,
                 font=(FONT, 8)).pack(anchor="w")

        # --- academic ---
        ac = tk.LabelFrame(self, text=" Academic rules ", bg=CARD, font=(FONT, 10, "bold"), padx=16, pady=12)
        ac.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))
        tk.Label(ac, text="Pass percentage", bg=CARD).grid(row=0, column=0, sticky="w", pady=6)
        tk.Spinbox(ac, from_=0, to=100, increment=5, width=6, textvariable=app.pass_mark).grid(row=0, column=1, padx=10)
        tk.Label(ac, text="Used for red rows, pass-rate and report cards", bg=CARD, fg=MUTED,
                 font=(FONT, 8)).grid(row=1, column=0, columnspan=2, sticky="w")
        tk.Checkbutton(ac, text="Ask before deleting students", variable=app.confirm_delete,
                       bg=CARD, activebackground=CARD).grid(row=2, column=0, columnspan=2, sticky="w", pady=12)
        app.button(ac, "Set pass mark via dialog", self.ask_pass, kind="neutral").grid(
            row=3, column=0, columnspan=2, sticky="w")

        # --- data ---
        da = tk.LabelFrame(self, text=" Data management ", bg=CARD, font=(FONT, 10, "bold"), padx=16, pady=12)
        da.grid(row=1, column=0, columnspan=2, sticky="ew")
        app.button(da, "Backup data…", lambda: app.main.backup(), kind="success").pack(side="left")
        app.button(da, "Export CSV…", lambda: app.main.pages["students"].export_csv(), kind="neutral").pack(side="left", padx=8)
        app.button(da, "Reset to sample data", self.reset_data, kind="danger").pack(side="left")

    def pick_colour(self):
        colour = colorchooser.askcolor(color=self.app.accent, title="Choose accent colour")[1]
        if colour:
            self.app.apply_accent(colour)

    def change_font(self, value):
        size = int(float(value))
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
            tkfont.nametofont(name).configure(size=size)
        ttk.Style().configure("Treeview", rowheight=int(size * 2.8))

    def ask_pass(self):
        v = simpledialog.askinteger("Pass mark", "Enter pass percentage (0-100):",
                                    initialvalue=self.app.pass_mark.get(), minvalue=0, maxvalue=100)
        if v is not None:
            self.app.pass_mark.set(v)

    def reset_data(self):
        if messagebox.askyesno("Reset", "Replace ALL data with fresh sample data?", icon="warning"):
            self.app.store.seed()
            self.app.log("Data reset to sample data")
            self.app.set_status("Sample data restored")


# ----------------------------------------------------------------------------
if __name__ == "__main__":
    App().mainloop()