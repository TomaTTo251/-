import tkinter as tk
from tkinter import font as tkfont
import threading
from pynput import keyboard, mouse
from pynput.mouse import Button, Controller as MouseController

mouse_ctrl = MouseController()
holding = False
kb_listener = None
ms_listener = None
hotkey = None
hotkey_type = None  # 'keyboard' or 'mouse'
hotkey_display = None
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

# --- Keyboard listener ---
def on_key_press(key):
    if hotkey_type == 'keyboard' and key == hotkey:
        root.after(0, lambda: set_holding(not holding))

def start_kb_listener():
    global kb_listener
    if kb_listener:
        kb_listener.stop()
    kb_listener = keyboard.Listener(on_press=on_key_press)
    kb_listener.daemon = True
    kb_listener.start()

# --- Mouse listener ---
MOUSE_BUTTON_NAMES = {
    Button.x1: "Кнопка мыши 4",
    Button.x2: "Кнопка мыши 5",
    Button.middle: "Средняя кнопка",
    Button.right: "Правая кнопка",
    Button.left: "Левая кнопка",
}

def on_mouse_click(x, y, button, pressed):
    global recording
    if recording and pressed:
        # ignore left click during recording (it's used to click the button)
        if button == Button.left:
            return
        recording = False
        set_hotkey_mouse(button)
        return
    if not recording and hotkey_type == 'mouse' and button == hotkey and pressed:
        root.after(0, lambda: set_holding(not holding))

def start_ms_listener():
    global ms_listener
    if ms_listener:
        ms_listener.stop()
    ms_listener = mouse.Listener(on_click=on_mouse_click)
    ms_listener.daemon = True
    ms_listener.start()

def set_hotkey_mouse(button):
    global hotkey, hotkey_type, hotkey_display
    hotkey = button
    hotkey_type = 'mouse'
    hotkey_display = MOUSE_BUTTON_NAMES.get(button, str(button))
    hotkey_label.config(text=f"[ {hotkey_display} ]")
    record_btn.config(text="Назначить клавишу", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")
    start_kb_listener()
    start_ms_listener()

# --- Recording ---
def start_recording():
    global recording
    recording = True
    record_btn.config(text="Нажми клавишу или кнопку мыши...", bg="#1e3a5f", state="disabled")
    hotkey_label.config(text="—")
    root.focus_force()
    root.bind("<KeyPress>", capture_key)
    start_ms_listener()

def capture_key(event):
    global hotkey, hotkey_type, recording
    if not recording:
        return
    recording = False

    key_name = event.keysym
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

    hotkey_type = 'keyboard'
    hotkey_label.config(text=f"[ {display} ]")
    record_btn.config(text="Назначить клавишу", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")
    start_kb_listener()
    start_ms_listener()

def on_close():
    global holding
    if holding:
        mouse_ctrl.release(Button.left)
    if kb_listener:
        kb_listener.stop()
    if ms_listener:
        ms_listener.stop()
    root.destroy()

# --- UI ---
root = tk.Tk()
root.title("AutoClick Toggle")
root.geometry("360x360")
root.resizable(False, False)
root.configure(bg="#0f172a")
root.protocol("WM_DELETE_WINDOW", on_close)

title_font  = tkfont.Font(family="Segoe UI", size=15, weight="bold")
sub_font    = tkfont.Font(family="Segoe UI", size=8, weight="bold")
label_font  = tkfont.Font(family="Segoe UI", size=10)
key_font    = tkfont.Font(family="Consolas", size=16, weight="bold")
status_font = tkfont.Font(family="Segoe UI", size=12, weight="bold")

tk.Label(root, text="AutoClick Toggle", font=title_font,
         bg="#0f172a", fg="#e2e8f0").pack(pady=(20, 0))

tk.Label(root, text="Никита Жирный Качёк Грелд", font=sub_font,
         bg="#0f172a", fg="#f59e0b").pack(pady=(2, 4))

tk.Label(root, text="Нажми клавишу один раз — ЛКМ зажата.\nЕщё раз — отпущена.",
         font=label_font, bg="#0f172a", fg="#94a3b8", justify="center").pack(pady=(0, 16))

tk.Label(root, text="Текущая клавиша", font=label_font,
         bg="#0f172a", fg="#64748b").pack()

hotkey_label = tk.Label(root, text="—", font=key_font,
                        bg="#0f172a", fg="#38bdf8")
hotkey_label.pack(pady=(2, 14))

record_btn = tk.Button(root, text="Назначить клавишу",
                       font=label_font, bg="#1e40af", fg="white",
                       activebackground="#1e3a8a", activeforeground="white",
                       relief="flat", padx=16, pady=8, cursor="hand2",
                       command=start_recording)
record_btn.pack(pady=(0, 18))

status_label = tk.Label(root, text="🔴 ЛКМ отпущена", font=status_font,
                        bg="#0f172a", fg="#f87171")
status_label.pack()

start_ms_listener()
root.mainloop()
