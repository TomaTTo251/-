import tkinter as tk
from tkinter import font as tkfont
import threading
from pynput import keyboard, mouse
from pynput.mouse import Button, Controller as MouseController

mouse_ctrl = MouseController()
holding = False
listener = None
hotkey = None
recording = False

def set_holding(state):
    global holding
    holding = state
    if state:
        mouse_ctrl.press(Button.left)
        status_label.config(text="🟢 ЛКМ зажата", fg="#4ade80")
    else:
        mouse_ctrl.release(Button.left)
        status_label.config(text="🔴 ЛКМ отпущена", fg="#f87171")

def on_key_press(key):
    global holding
    if key == hotkey:
        root.after(0, lambda: set_holding(not holding))

def start_listener():
    global listener
    if listener:
        listener.stop()
    listener = keyboard.Listener(on_press=on_key_press)
    listener.daemon = True
    listener.start()

def start_recording():
    global recording
    recording = True
    record_btn.config(text="Нажми клавишу...", bg="#1e3a5f", state="disabled")
    hotkey_label.config(text="—")
    root.focus_force()
    root.bind("<KeyPress>", capture_key)

def capture_key(event):
    global hotkey, recording
    if not recording:
        return
    recording = False

    key_name = event.keysym
    # Map to pynput key
    special_map = {
        "F1": keyboard.Key.f1, "F2": keyboard.Key.f2, "F3": keyboard.Key.f3,
        "F4": keyboard.Key.f4, "F5": keyboard.Key.f5, "F6": keyboard.Key.f6,
        "F7": keyboard.Key.f7, "F8": keyboard.Key.f8, "F9": keyboard.Key.f9,
        "F10": keyboard.Key.f10, "F11": keyboard.Key.f11, "F12": keyboard.Key.f12,
        "Insert": keyboard.Key.insert, "Delete": keyboard.Key.delete,
        "Home": keyboard.Key.home, "End": keyboard.Key.end,
        "Prior": keyboard.Key.page_up, "Next": keyboard.Key.page_down,
        "Caps_Lock": keyboard.Key.caps_lock, "Scroll_Lock": keyboard.Key.scroll_lock,
        "Num_Lock": keyboard.Key.num_lock,
        "Tab": keyboard.Key.tab, "BackSpace": keyboard.Key.backspace,
        "Return": keyboard.Key.enter, "Escape": keyboard.Key.esc,
        "space": keyboard.Key.space,
        "Up": keyboard.Key.up, "Down": keyboard.Key.down,
        "Left": keyboard.Key.left, "Right": keyboard.Key.right,
        "grave": keyboard.KeyCode.from_char("`"),
        "minus": keyboard.KeyCode.from_char("-"),
        "equal": keyboard.KeyCode.from_char("="),
        "bracketleft": keyboard.KeyCode.from_char("["),
        "bracketright": keyboard.KeyCode.from_char("]"),
        "semicolon": keyboard.KeyCode.from_char(";"),
        "apostrophe": keyboard.KeyCode.from_char("'"),
        "backslash": keyboard.KeyCode.from_char("\\"),
        "comma": keyboard.KeyCode.from_char(","),
        "period": keyboard.KeyCode.from_char("."),
        "slash": keyboard.KeyCode.from_char("/"),
    }

    if key_name in special_map:
        hotkey = special_map[key_name]
        display = key_name
    elif len(key_name) == 1:
        hotkey = keyboard.KeyCode.from_char(key_name.lower())
        display = key_name.upper()
    else:
        hotkey = None
        hotkey_label.config(text="Не поддерживается")
        record_btn.config(text="Назначить клавишу", bg="#1e40af", state="normal")
        root.unbind("<KeyPress>")
        return

    hotkey_label.config(text=f"[ {display} ]")
    record_btn.config(text="Назначить клавишу", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")
    start_listener()

def on_close():
    global holding
    if holding:
        mouse_ctrl.release(Button.left)
    if listener:
        listener.stop()
    root.destroy()

# --- UI ---
root = tk.Tk()
root.title("AutoClick Toggle")
root.geometry("320x300")
root.resizable(False, False)
root.configure(bg="#0f172a")
root.protocol("WM_DELETE_WINDOW", on_close)

title_font = tkfont.Font(family="Segoe UI", size=15, weight="bold")
label_font = tkfont.Font(family="Segoe UI", size=10)
key_font   = tkfont.Font(family="Consolas", size=18, weight="bold")
status_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")

tk.Label(root, text="AutoClick Toggle", font=title_font,
         bg="#0f172a", fg="#e2e8f0").pack(pady=(24, 4))

tk.Label(root, text="Нажми клавишу один раз — ЛКМ зажата.\nЕщё раз — отпущена.",
         font=label_font, bg="#0f172a", fg="#94a3b8", justify="center").pack(pady=(0, 20))

tk.Label(root, text="Текущая клавиша", font=label_font,
         bg="#0f172a", fg="#64748b").pack()

hotkey_label = tk.Label(root, text="—", font=key_font,
                        bg="#0f172a", fg="#38bdf8")
hotkey_label.pack(pady=(2, 16))

record_btn = tk.Button(root, text="Назначить клавишу",
                       font=label_font, bg="#1e40af", fg="white",
                       activebackground="#1e3a8a", activeforeground="white",
                       relief="flat", padx=16, pady=8, cursor="hand2",
                       command=start_recording)
record_btn.pack(pady=(0, 20))

status_label = tk.Label(root, text="🔴 ЛКМ отпущена", font=status_font,
                        bg="#0f172a", fg="#f87171")
status_label.pack()

root.mainloop()
