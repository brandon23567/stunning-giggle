# 🎓 Student Management System

A multi-page desktop application built with **Python and Tkinter** for managing student records, marks and reports. It uses only the Python standard library, so there is nothing to install beyond Python itself.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

This project was created for **Python Experiment 6** and extended into a mini project. It also works as a guided tour of Tkinter: nearly every standard widget, geometry manager and styling option is used somewhere in the app, and a built-in **Widget Lab** page demonstrates them side by side.

---

## 📸 Screenshots

| Login | Dashboard |
|:---:|:---:|
| ![Login](screenshots/01_login.png) | ![Dashboard](screenshots/02_dashboard.png) |

| Student records | Add / edit form |
|:---:|:---:|
| ![Students](screenshots/03_students.png) | ![Form](screenshots/04_student_form.png) |

| Report card | Widget Lab |
|:---:|:---:|
| ![Report card](screenshots/05_report_card.png) | ![Widget Lab](screenshots/06_widget_lab_appearance.png) |

| Geometry managers demo | Custom accent colour |
|:---:|:---:|
| ![Geometry](screenshots/07_widget_lab_geometry.png) | ![Teal theme](screenshots/08_theme_teal.png) |

---

## ✨ Features

### Student management
- **Add, edit and delete** students (multi-select delete with confirmation)
- **Live search** by name, email or ID, plus a **course filter**
- **Click-to-sort** on any column, striped rows, and **red highlighting** for students below the pass mark
- **Right-click context menu** and double-click to edit
- **Export to CSV** and **backup** of the data file
- Form **validation**: name and email patterns, phone field that only accepts digits (max 10)

### Academic records
- Enter marks for four subjects using sliders or spin boxes, with a live total, percentage and grade
- Formatted, colour-coded **report card** with a copy-to-clipboard button
- **Class ranking** table with the top three highlighted
- Attendance tracking

### Dashboard
- Summary cards: total students, average marks, pass rate, hostel residents
- Hand-drawn **bar chart** (students per course) using the Canvas widget, with hover highlighting
- Recent activity log, progress bars and a live clock

### Interface and customisation
- Sidebar navigation, menu bar and **keyboard shortcuts**
- **Accent colour themes**: four presets or any custom colour from the colour chooser
- Adjustable font size, pass percentage and delete-confirmation setting
- Login screen with a show-password option and a **5-second lock-out** after 3 failed attempts
- Data saved automatically to a local JSON file

---

## 🚀 Getting Started

### Requirements
- **Python 3.8 or newer**
- **Tkinter** (included with Python on Windows and macOS)

On Linux, install Tkinter if it is missing:

```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

Check that it works:

```bash
python -m tkinter
```

A small test window should appear.

### Run the app

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
python experiment6_student_management.py
```

Use `python3` instead of `python` if that is how Python is installed on your system.

### Login

| Username | Password |
|---|---|
| `admin` | `admin123` |

On the first run the app creates `students.json` in the same folder and fills it with 12 sample students. Delete that file, or use **Settings → Reset to sample data**, to start over.

---

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Enter` | Log in (on the login screen) |
| `Ctrl + 1` … `Ctrl + 6` | Go to Dashboard, Students, Add Student, Marks & Reports, Widget Lab, Settings |
| `Ctrl + N` | New student |
| `Ctrl + Q` | Quit |
| `Delete` | Delete selected students (in the student table) |
| `Double-click` a row | Edit that student |
| `Right-click` a row | Open the context menu |

---

## 🗂️ Project structure

```
.
├── experiment6_student_management.py   # the whole application
├── students.json                       # created on first run (your data)
├── screenshots/                        # images used in this README
└── README.md
```

### Code overview

The application is written in an object-oriented style, with one class per screen:

| Class | Responsibility |
|---|---|
| `DataStore` | Loads and saves students in `students.json`; generates sample data |
| `App(tk.Tk)` | Root window; holds shared state, ttk styles, theme handling and button/entry helpers |
| `LoginPage` | Login screen with lock-out logic |
| `MainFrame` | Menu bar, sidebar, header, clock, status bar and page switching |
| `DashboardPage` | Statistic cards, Canvas chart, activity list, progress bars |
| `StudentsPage` | Searchable and sortable `Treeview`, context menu, CSV export |
| `StudentFormPage` | Add / edit form with validation |
| `MarksPage` | Notebook with marks entry, report card and class ranking |
| `WidgetLabPage` | Interactive demonstration of Tkinter widgets, options, events and dialogs |
| `SettingsPage` | Theme, font size, pass mark and data tools |

### How navigation works
All pages are `Frame` objects placed in the same grid cell. Switching a page just calls `tkraise()` on it, and an optional `on_show()` method refreshes its data. The login screen and main application are swapped with `pack_forget()` and `destroy()`.

### Data model
Each student is stored as a JSON object:

```json
{
  "id": 1,
  "name": "Aarav Sharma",
  "age": 20,
  "gender": "Male",
  "email": "aarav1@college.edu",
  "phone": "9876543210",
  "course": "B.Tech CSE",
  "semester": 4,
  "scholarship": "Merit",
  "skills": ["Python", "Java", "Sports"],
  "hostel": true,
  "address": "12, Model Town, Ludhiana",
  "marks": {"Maths": 78, "Physics": 65, "Programming": 82, "English": 70},
  "attendance": 88
}
```

---

## 🧩 Tkinter concepts demonstrated

| Area | What is used |
|---|---|
| **Containers** | `Tk`, `Toplevel`, `Frame`, `LabelFrame`, `PanedWindow`, `ttk.Notebook` |
| **Display** | `Label`, `Message`, `Canvas`, `ttk.Progressbar`, `ttk.Separator`, `PhotoImage` |
| **Input** | `Button`, `Entry`, `Text`, `Checkbutton`, `Radiobutton`, `Spinbox`, `Scale`, `Listbox`, `OptionMenu`, `Menubutton`, `ttk.Combobox`, `Scrollbar` |
| **Data** | `ttk.Treeview` with sorting, tags and scrollbars |
| **Menus** | Menu bar, drop-down menus, check/radio items, right-click pop-up menu |
| **Dialogs** | `messagebox`, `filedialog`, `simpledialog`, `colorchooser` |
| **Layout** | `pack`, `grid` (weights, `sticky`, spans, `uniform`), `place` (relative positioning) |
| **Styling** | Colours, fonts, `relief`, borders, `cursor`, images, `ttk.Style` (`configure` and `map`), runtime theme switching |
| **Events** | `command=`, `bind()`, `<Enter>`/`<Leave>` hover, `<<ComboboxSelected>>`, `after()`, `protocol()`, `trace_add()`, `validatecommand` |
| **Variables** | `StringVar`, `IntVar`, `BooleanVar` |

The **Widget Lab** page in the app lets you see and try most of these live.

---

## 🛠️ Customisation

Constants near the top of `experiment6_student_management.py` are easy to change:

- `COURSES`, `SUBJECTS`, `SKILLS`, `SCHOLARSHIPS` – the lists used in forms and charts
- `ACCENT_PRESETS` – the theme colours offered in Settings
- `BG`, `CARD`, `TEXT`, `MUTED`, `FONT` – the base palette and font
- `LoginPage.USER` and `LoginPage.PASSWORD` – the demo login

---

## ❓ Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'tkinter'` | Install Tkinter (see [Requirements](#requirements)) |
| Window opens too large or small | Change the `geometry()` line in `App.__init__` |
| Emoji icons look plain or show as boxes | They depend on the system emoji font; the app still works normally |
| Data seems wrong or corrupted | Delete `students.json` and restart, or use Settings → Reset to sample data |
| Running on a server with no display | Tkinter needs a graphical display; run it on a desktop machine |

---

## 🔮 Possible improvements

- Use SQLite instead of a JSON file
- Store hashed passwords and support multiple users and roles
- Charts for marks distribution (embedding Matplotlib in Tkinter)
- Import students from CSV
- Print or export report cards to PDF
- Dark mode

---

## 👤 Author

**Brandon Mahuvava** – Roll No. `26MCC20020`
Department of MCA Cloud Computing & Devops, *Chandigarh University*

Created as part of the Python Programming laboratory (Experiment 6) and mini project.

---

## 📄 License

This project is released under the MIT License. Add a `LICENSE` file to your repository if you want to make this official, or remove this section if your course requires otherwise.
