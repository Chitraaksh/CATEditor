from tkinter import *
from tkinter.filedialog import *
from tkinter.messagebox import *
from tkinter.font import Font, families
from tkinter.scrolledtext import *
from tkinter.colorchooser import askcolor
from tkinter.simpledialog import askstring
import time
import sys
import re
import os
import subprocess

root = Tk()

root.title("Text Editor-Untiltled")
root.geometry("300x250+300+300")
root.minsize(width=400, height=400)

# --- Language and file extension mapping ---
LANG_EXT = {"C": "c", "C++": "cpp", "Python": "py"}
selected_language = "Python"  # Default language

# --- .temp folder and file setup ---
TEMP_DIR = ".temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def get_temp_file():
    ext = LANG_EXT.get(selected_language, "txt")
    return os.path.join(TEMP_DIR, f"tempeditormodified.{ext}")

# --- Load last saved file if exists ---
def load_last_file():
    temp_file = get_temp_file()
    if os.path.exists(temp_file):
        with open(temp_file, "r", encoding="utf-8") as f:
            text.delete("1.0", END)
            text.insert("1.0", f.read())

# --- Save file every 2 seconds ---
def autosave():
    temp_file = get_temp_file()
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(text.get("1.0", END))
    root.after(2000, autosave)

text = ScrolledText(
    root,
    state='normal',
    height=400,
    width=400,
    wrap='word',
    pady=2,
    padx=3,
    undo=True,
    bg='#1a1a1a',      # background color
    fg='#ffffe1'       # foreground (text) color
)
text.pack(fill=Y, expand=1)
text.focus_set()

menubar = Menu(root)

# --- File Menu ---
class File():
    def newFile(self):
        self.filename = "Untitled"
        self.text.delete(0.0, END)

    def saveFile(self):
        try:
            t = self.text.get(0.0, END)
            f = open(self.filename, 'w')
            f.write(t)
            f.close()
        except:
            self.saveAs()

    def saveAs(self):
        f = asksaveasfile(mode='w', defaultextension='.txt')
        t = self.text.get(0.0, END)
        try:
            f.write(t.rstrip())
        except:
            showerror(title="Oops!", message="Unable to save file...")

    def openFile(self):
        f = askopenfile(mode='r')
        self.filename = f.name
        t = f.read()
        self.text.delete(0.0, END)
        self.text.insert(0.0, t)

    def quit(self):
        entry = askyesno(title="Quit", message="Are you sure you want to quit?")
        if entry == True:
            self.root.destroy()

    def __init__(self, text, root):
        self.filename = None
        self.text = text
        self.root = root

def file_menu_main(root, text, menubar):
    filemenu = Menu(menubar)
    objFile = File(text, root)
    filemenu.add_command(label="New", command=objFile.newFile)
    filemenu.add_command(label="Open", command=objFile.openFile)
    filemenu.add_command(label="Save", command=objFile.saveFile)
    filemenu.add_command(label="Save As...", command=objFile.saveAs)
    filemenu.add_separator()
    filemenu.add_command(label="Quit", command=objFile.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    root.config(menu=menubar)

# --- Edit Menu ---
class Edit():
    def popup(self, event):
        self.rightClick.post(event.x_root, event.y_root)

    def copy(self, *args):
        sel = self.text.selection_get()
        self.clipboard = sel

    def cut(self, *args):
        sel = self.text.selection_get()
        self.clipboard = sel
        self.text.delete(SEL_FIRST, SEL_LAST)

    def paste(self, *args):
        self.text.insert(INSERT, self.clipboard)

    def selectAll(self, *args):
        self.text.tag_add(SEL, "1.0", END)
        self.text.mark_set(0.0, END)
        self.text.see(INSERT)

    def undo(self, *args):
        self.text.edit_undo()

    def redo(self, *args):
        self.text.edit_redo()

    def find(self, *args):
        self.text.tag_remove('found', '1.0', END)
        target = askstring('Find', 'Search String:')
        if target:
            idx = '1.0'
            while 1:
                idx = self.text.search(target, idx, nocase=1, stopindex=END)
                if not idx: break
                lastidx = '%s+%dc' % (idx, len(target))
                self.text.tag_add('found', idx, lastidx)
                idx = lastidx
            self.text.tag_config('found', foreground='white', background='blue')

    def __init__(self, text, root):
        self.clipboard = None
        self.text = text
        self.rightClick = Menu(root)

def edit_menu_main(root, text, menubar):
    objEdit = Edit(text, root)
    editmenu = Menu(menubar)
    editmenu.add_command(label="Copy", command=objEdit.copy, accelerator="Ctrl+C")
    editmenu.add_command(label="Cut", command=objEdit.cut, accelerator="Ctrl+X")
    editmenu.add_command(label="Paste", command=objEdit.paste, accelerator="Ctrl+V")
    editmenu.add_command(label="Undo", command=objEdit.undo, accelerator="Ctrl+Z")
    editmenu.add_command(label="Redo", command=objEdit.redo, accelerator="Ctrl+Y")
    editmenu.add_command(label="Find", command=objEdit.find, accelerator="Ctrl+F")
    editmenu.add_separator()
    editmenu.add_command(label="Select All", command=objEdit.selectAll, accelerator="Ctrl+A")
    menubar.add_cascade(label="Edit", menu=editmenu)

    root.bind_all("<Control-z>", objEdit.undo)
    root.bind_all("<Control-y>", objEdit.redo)
    root.bind_all("<Control-f>", objEdit.find)
    root.bind_all("Control-a", objEdit.selectAll)

    objEdit.rightClick.add_command(label="Copy", command=objEdit.copy)
    objEdit.rightClick.add_command(label="Cut", command=objEdit.cut)
    objEdit.rightClick.add_command(label="Paste", command=objEdit.paste)
    objEdit.rightClick.add_separator()
    objEdit.rightClick.add_command(label="Select All", command=objEdit.selectAll)
    objEdit.rightClick.bind("<Control-q>", objEdit.selectAll)

    text.bind("<Button-3>", objEdit.popup)

    root.config(menu=menubar)

# --- Format Menu ---
class Format():
    def __init__(self, text):
        self.text = text

    def changeBg(self):
        (triple, hexstr) = askcolor()
        if hexstr:
            self.text.config(bg=hexstr)

    def changeFg(self):
        (triple, hexstr) = askcolor()
        if hexstr:
            self.text.config(fg=hexstr)

    def bold(self, *args):
        try:
            current_tags = self.text.tag_names("sel.first")
            if "bold" in current_tags:
                self.text.tag_remove("bold", "sel.first", "sel.last")
            else:
                self.text.tag_add("bold", "sel.first", "sel.last")
                bold_font = Font(self.text, self.text.cget("font"))
                bold_font.configure(weight="bold")
                self.text.tag_configure("bold", font=bold_font)
        except:
            pass

    def italic(self, *args):
        try:
            current_tags = self.text.tag_names("sel.first")
            if "italic" in current_tags:
                self.text.tag_remove("italic", "sel.first", "sel.last")
            else:
                self.text.tag_add("italic", "sel.first", "sel.last")
                italic_font = Font(self.text, self.text.cget("font"))
                italic_font.configure(slant="italic")
                self.text.tag_configure("italic", font=italic_font)
        except:
            pass

    def underline(self, *args):
        try:
            current_tags = self.text.tag_names("sel.first")
            if "underline" in current_tags:
                self.text.tag_remove("underline", "sel.first", "sel.last")
            else:
                self.text.tag_add("underline", "sel.first", "sel.last")
                underline_font = Font(self.text, self.text.cget("font"))
                underline_font.configure(underline=1)
                self.text.tag_configure("underline", font=underline_font)
        except:
            pass

    def overstrike(self, *args):
        try:
            current_tags = self.text.tag_names("sel.first")
            if "overstrike" in current_tags:
                self.text.tag_remove("overstrike", "sel.first", "sel.last")
            else:
                self.text.tag_add("overstrike", "sel.first", "sel.last")
                overstrike_font = Font(self.text, self.text.cget("font"))
                overstrike_font.configure(overstrike=1)
                self.text.tag_configure("overstrike", font=overstrike_font)
        except:
            pass

    def addDate(self):
        full_date = time.localtime()
        day = str(full_date.tm_mday)
        month = str(full_date.tm_mon)
        year = str(full_date.tm_year)
        date = day + '/' + month + '/' + year
        self.text.insert(INSERT, date, "a")

def format_menu_main(root, text, menubar):
    objFormat = Format(text)
    fontoptions = families(root)
    font = Font(family="Arial", size=10)
    text.configure(font=font)
    formatMenu = Menu(menubar)
    fsubmenu = Menu(formatMenu, tearoff=0)
    ssubmenu = Menu(formatMenu, tearoff=0)
    for option in fontoptions:
        fsubmenu.add_command(label=option, command=lambda option=option: font.configure(family=option))
    for value in range(1, 31):
        ssubmenu.add_command(label=str(value), command=lambda value=value: font.configure(size=value))
    formatMenu.add_command(label="Change Background", command=objFormat.changeBg)
    formatMenu.add_command(label="Change Font Color", command=objFormat.changeFg)
    formatMenu.add_cascade(label="Font", underline=0, menu=fsubmenu)
    formatMenu.add_cascade(label="Size", underline=0, menu=ssubmenu)
    formatMenu.add_command(label="Bold", command=objFormat.bold, accelerator="Ctrl+B")
    formatMenu.add_command(label="Italic", command=objFormat.italic, accelerator="Ctrl+I")
    formatMenu.add_command(label="Underline", command=objFormat.underline, accelerator="Ctrl+U")
    formatMenu.add_command(label="Overstrike", command=objFormat.overstrike, accelerator="Ctrl+T")
    formatMenu.add_command(label="Add Date", command=objFormat.addDate)
    menubar.add_cascade(label="Format", menu=formatMenu)
    root.bind_all("<Control-b>", objFormat.bold)
    root.bind_all("<Control-i>", objFormat.italic)
    root.bind_all("<Control-u>", objFormat.underline)
    root.bind_all("<Control-T>", objFormat.overstrike)
    root.grid_columnconfigure(0, weight=1)
    root.resizable(True, True)
    root.config(menu=menubar)

# --- Help Menu ---
class Help():
    def about(root):
        showinfo(title="About", message="This a simple text editor implemented in Python's Tkinter")

def help_menu_main(root, text, menubar):
    help = Help()
    helpMenu = Menu(menubar)
    helpMenu.add_command(label="About", command=help.about)
    menubar.add_cascade(label="Help", menu=helpMenu)
    root.config(menu=menubar)

# --- Syntax Highlighting Implementation ---
def apply_highlighting(keywords, strings, comments, libraries=None, functions=None, return_values=None):
    text.tag_remove("keyword", "1.0", END)
    text.tag_remove("string", "1.0", END)
    text.tag_remove("comment", "1.0", END)
    text.tag_remove("library", "1.0", END)
    text.tag_remove("function", "1.0", END)
    text.tag_remove("return-value", "1.0", END)

    content = text.get("1.0", END)
    for match in re.finditer(keywords, content, re.MULTILINE):
        start, end = f"1.0+{match.start()}c", f"1.0+{match.end()}c"
        text.tag_add("keyword", start, end)
    for match in re.finditer(strings, content, re.MULTILINE):
        start, end = f"1.0+{match.start()}c", f"1.0+{match.end()}c"
        text.tag_add("string", start, end)
    for match in re.finditer(comments, content, re.MULTILINE | re.DOTALL):
        start, end = f"1.0+{match.start()}c", f"1.0+{match.end()}c"
        text.tag_add("comment", start, end)
    if libraries:
        for match in re.finditer(libraries, content, re.MULTILINE):
            start, end = f"1.0+{match.start()}c", f"1.0+{match.end()}c"
            text.tag_add("library", start, end)
    if functions:
        for match in re.finditer(functions, content, re.MULTILINE):
            start, end = f"1.0+{match.start()}c", f"1.0+{match.end()}c"
            text.tag_add("function", start, end)
    if return_values:
        for match in re.finditer(return_values, content, re.MULTILINE):
            start, end = f"1.0+{match.start()}c", f"1.0+{match.end()}c"
            text.tag_add("return-value", start, end)

def highlight_python_syntax():
    keywords = r"\b(def|class|import|from|if|else|elif|for|while|return|try|except|finally|with|as|pass|break|continue|lambda|yield|in|is|not|and|or)\b"
    strings = r"(['\"].*?['\"])"
    comments = r"(#.*?$)"
    functions = r"\bdef\s+(\w+)"
    return_values = r"return\s+[\w\.]+"
    apply_highlighting(keywords, strings, comments, functions=functions, return_values=return_values)

def highlight_c_syntax():
    keywords = r"\b(int|float|double|char|if|else|for|while|return|void|struct|typedef|switch|case|break|continue|default|sizeof|do|static|const|goto|enum|union|extern)\b"
    strings = r"(['\"].*?['\"])"
    comments = r"(//.*?$|/\*.*?\*/)"
    libraries = r"#include\s*<([\w\.]+)>"
    functions = r"\b\w+\s*(?=\()"
    return_values = r"return\s+[\w\.]+"
    apply_highlighting(keywords, strings, comments, libraries, functions, return_values)

def highlight_cpp_syntax():
    keywords = r"\b(int|float|double|char|if|else|for|while|return|void|struct|typedef|switch|case|break|continue|default|sizeof|do|static|const|goto|enum|union|extern|class|public|private|protected|virtual|namespace|using|new|delete|try|catch|throw|template|typename|this|operator|friend|inline|override|final)\b"
    strings = r"(['\"].*?['\"])"
    comments = r"(//.*?$|/\*.*?\*/)"
    libraries = r"#include\s*<([\w\.]+)>"
    functions = r"\b\w+\s*(?=\()"
    return_values = r"return\s+[\w\.]+"
    apply_highlighting(keywords, strings, comments, libraries, functions, return_values)

def apply_syntax_highlighting(event=None):
    if selected_language == "Python":
        highlight_python_syntax()
    elif selected_language == "C":
        highlight_c_syntax()
    elif selected_language == "C++":
        highlight_cpp_syntax()

# --- Font Fix for Highlighting ---
base_font = Font(font=text.cget("font"))
keyword_font = Font(family=base_font.actual("family"), size=base_font.actual("size"), weight="bold")
string_font = Font(family=base_font.actual("family"), size=base_font.actual("size"))
comment_font = Font(family=base_font.actual("family"), size=base_font.actual("size"), slant="italic")

text.tag_configure("keyword", foreground="#00e6f6", font=keyword_font)
text.tag_configure("string", foreground="#7fffd4", font=string_font)
text.tag_configure("comment", foreground="#aaaaaa", font=comment_font)
text.tag_configure("library", foreground="#4682b4", font=string_font)
text.tag_configure("function", foreground="#ff69b4", font=string_font)
text.tag_configure("return-value", foreground="#ff6347", font=string_font)

# --- Language Tab ---
def set_language(lang):
    global selected_language
    selected_language = lang
    menubar.entryconfig(language_menu_index, label=lang)
    apply_syntax_highlighting()
    load_last_file()  # Load the last file for the selected language

language_menu = Menu(menubar, tearoff=0)
for lang in ["C", "C++", "Python"]:
    language_menu.add_command(label=lang, command=lambda l=lang: set_language(l))
menubar.add_cascade(label="Language", menu=language_menu)
language_menu_index = menubar.index("Language")

# --- Run Button ---
def run_code():
    temp_file = get_temp_file()
    autosave()  # Ensure latest content is saved before running
    if selected_language == "Python":
        cmd = ["py", temp_file]
    elif selected_language == "C":
        exe_file = os.path.join(TEMP_DIR, "tempeditormodified_c_exe")
        compile_cmd = ["gcc", temp_file, "-o", exe_file]
        try:
            subprocess.run(compile_cmd, check=True)
            cmd = [exe_file]
        except Exception as e:
            showerror("Run Error", f"Compilation failed:\n{e}")
            return
    elif selected_language == "C++":
        exe_file = os.path.join(TEMP_DIR, "tempeditormodified_cpp_exe")
        compile_cmd = ["g++", temp_file, "-o", exe_file]
        try:
            subprocess.run(compile_cmd, check=True)
            cmd = [exe_file]
        except Exception as e:
            showerror("Run Error", f"Compilation failed:\n{e}")
            return
    else:
        showerror("Run Error", "Unsupported language selected.")
        return

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = result.stdout + "\n" + result.stderr
        showinfo("Run Output", output)
    except Exception as e:
        showerror("Run Error", f"Execution failed:\n{e}")

run_menu = Menu(menubar, tearoff=0)
run_menu.add_command(label="Run", command=run_code)
menubar.add_cascade(label="Run", menu=run_menu)

# Bind the event to apply syntax highlighting on every key release
text.bind("<KeyRelease>", apply_syntax_highlighting)

# Add all menus
file_menu_main(root, text, menubar)
edit_menu_main(root, text, menubar)
format_menu_main(root, text, menubar)
help_menu_main(root, text, menubar)

root.config(menu=menubar)

# Load last file and start autosave
load_last_file()
autosave()

root.mainloop()