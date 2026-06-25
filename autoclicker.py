import tkinter as tk
from tkinter import font as tkfont, ttk, messagebox, filedialog
import threading
import time
import json
import os
from pynput import keyboard, mouse
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController

mouse_ctrl = MouseController()
kb_ctrl = KeyboardController()

MOUSE_BUTTON_NAMES = {
    Button.x1: "MOUSE4", Button.x2: "MOUSE5",
    Button.middle: "MOUSE3", Button.right: "MOUSE2", Button.left: "MOUSE1",
}
MOUSE_BUTTON_BY_NAME = {v: k for k, v in MOUSE_BUTTON_NAMES.items()}

# ── Toggle state ──────────────────────────────────────────────
holding = False
kb_listener = None
ms_listener = None
hotkey = None
hotkey_type = None
hold_target = None        # что зажимаем: ('mouse', Button) или ('key', key)
hold_target_display = "ЛКМ (MOUSE1)"
recording = False
recording_for = None      # 'hotkey' or 'target'

# ── Macro state ───────────────────────────────────────────────
macro_steps = []
macro_running = False
macro_thread = None
macro_hotkey = None
macro_hotkey_type = None
macro_recording_target = None

# ══════════════════════════════════════════════════════════════
#  LISTENERS
# ══════════════════════════════════════════════════════════════

def on_key_press(key):
    if recording or macro_recording_target is not None:
        return
    if hotkey_type == 'keyboard' and key == hotkey:
        root.after(0, lambda: set_holding(not holding))
    if macro_hotkey_type == 'keyboard' and key == macro_hotkey:
        root.after(0, toggle_macro)

def on_mouse_click(x, y, button, pressed):
    global recording, recording_for, macro_recording_target
    if recording and pressed and button != Button.left:
        rf = recording_for
        recording = False
        recording_for = None
        if rf == 'hotkey':
            root.after(0, lambda: set_toggle_hotkey_mouse(button))
        elif rf == 'target':
            root.after(0, lambda: set_hold_target_mouse(button))
        return
    if macro_recording_target == 'hotkey' and pressed and button != Button.left:
        root.after(0, lambda: set_macro_hotkey_mouse(button))
        return
    if not recording and macro_recording_target is None:
        if hotkey_type == 'mouse' and button == hotkey and pressed:
            root.after(0, lambda: set_holding(not holding))
        if macro_hotkey_type == 'mouse' and button == macro_hotkey and pressed:
            root.after(0, toggle_macro)

def start_listeners():
    global kb_listener, ms_listener
    for l in [kb_listener, ms_listener]:
        if l:
            try: l.stop()
            except: pass
    kb_listener = keyboard.Listener(on_press=on_key_press)
    kb_listener.daemon = True; kb_listener.start()
    ms_listener = mouse.Listener(on_click=on_mouse_click)
    ms_listener.daemon = True; ms_listener.start()

# ══════════════════════════════════════════════════════════════
#  TOGGLE TAB
# ══════════════════════════════════════════════════════════════

def press_target():
    if hold_target is None:
        mouse_ctrl.press(Button.left)
    elif hold_target[0] == 'mouse':
        mouse_ctrl.press(hold_target[1])
    elif hold_target[0] == 'key':
        try: kb_ctrl.press(hold_target[1])
        except: pass

def release_target():
    if hold_target is None:
        mouse_ctrl.release(Button.left)
    elif hold_target[0] == 'mouse':
        mouse_ctrl.release(hold_target[1])
    elif hold_target[0] == 'key':
        try: kb_ctrl.release(hold_target[1])
        except: pass

def set_holding(state):
    global holding
    holding = state
    if state:
        press_target()
        toggle_status.config(text=f"🟢 Зажато: {hold_target_display}", fg="#4ade80")
    else:
        release_target()
        toggle_status.config(text="🔴 Отпущено", fg="#f87171")

# ── Hotkey assignment ─────────────────────────────────────────

def set_toggle_hotkey_mouse(button):
    global hotkey, hotkey_type
    hotkey = button; hotkey_type = 'mouse'
    name = MOUSE_BUTTON_NAMES.get(button, str(button))
    toggle_hotkey_label.config(text=f"[ {name} ]")
    toggle_record_btn.config(text="Назначить", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")

def start_toggle_recording():
    global recording, recording_for
    recording = True; recording_for = 'hotkey'
    toggle_record_btn.config(text="Нажми...", bg="#1e3a5f", state="disabled")
    toggle_hotkey_label.config(text="—")
    root.focus_force()
    root.bind("<KeyPress>", capture_toggle_key)

def capture_toggle_key(event):
    global hotkey, hotkey_type, recording, recording_for
    if not recording: return
    recording = False; recording_for = None
    mapped = map_keysym(event.keysym)
    if mapped:
        hotkey = mapped[0]; hotkey_type = 'keyboard'
        toggle_hotkey_label.config(text=f"[ {mapped[1]} ]")
    else:
        toggle_hotkey_label.config(text="Не поддерживается")
    toggle_record_btn.config(text="Назначить", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")

# ── Hold target assignment ────────────────────────────────────

def set_hold_target_mouse(button):
    global hold_target, hold_target_display
    hold_target = ('mouse', button)
    hold_target_display = MOUSE_BUTTON_NAMES.get(button, str(button))
    toggle_target_label.config(text=f"[ {hold_target_display} ]")
    toggle_target_btn.config(text="Назначить", bg="#7c3aed", state="normal")
    root.unbind("<KeyPress>")

def start_target_recording():
    global recording, recording_for
    recording = True; recording_for = 'target'
    toggle_target_btn.config(text="Нажми...", bg="#4c1d95", state="disabled")
    toggle_target_label.config(text="—")
    root.focus_force()
    root.bind("<KeyPress>", capture_target_key)

def capture_target_key(event):
    global hold_target, hold_target_display, recording, recording_for
    if not recording: return
    recording = False; recording_for = None
    mapped = map_keysym(event.keysym)
    if mapped:
        hold_target = ('key', mapped[0])
        hold_target_display = mapped[1]
        toggle_target_label.config(text=f"[ {mapped[1]} ]")
    else:
        toggle_target_label.config(text="Не поддерживается")
    toggle_target_btn.config(text="Назначить", bg="#7c3aed", state="normal")
    root.unbind("<KeyPress>")

# ══════════════════════════════════════════════════════════════
#  MACRO TAB
# ══════════════════════════════════════════════════════════════

def toggle_macro():
    global macro_running, macro_thread
    if macro_running:
        macro_running = False
        macro_status.config(text="⏹ Остановлено", fg="#f87171")
        macro_run_btn.config(text="▶ Запустить")
    else:
        if not macro_steps:
            messagebox.showwarning("Макро", "Добавь хотя бы один шаг!")
            return
        macro_running = True
        macro_status.config(text="🟢 Выполняется...", fg="#4ade80")
        macro_run_btn.config(text="⏹ Остановить")
        macro_thread = threading.Thread(target=run_macro, daemon=True)
        macro_thread.start()

def run_macro():
    global macro_running
    repeat = macro_repeat_var.get()
    count = 0
    while macro_running:
        for step in macro_steps:
            if not macro_running: break
            execute_step(step)
        count += 1
        if repeat != 0 and count >= repeat:
            break
    macro_running = False
    root.after(0, lambda: macro_status.config(text="⏹ Завершено", fg="#94a3b8"))
    root.after(0, lambda: macro_run_btn.config(text="▶ Запустить"))

def execute_step(step):
    action = step['action']
    button = step.get('button', '')
    duration = step.get('duration', 0)
    delay_after = step.get('delay_after', 0)
    if action == 'hold_mouse':
        btn = MOUSE_BUTTON_BY_NAME.get(button, Button.left)
        mouse_ctrl.press(btn)
        if duration > 0:
            time.sleep(duration / 1000)
            mouse_ctrl.release(btn)
    elif action == 'release_mouse':
        btn = MOUSE_BUTTON_BY_NAME.get(button, Button.left)
        mouse_ctrl.release(btn)
    elif action == 'hold_key':
        try:
            k = getattr(keyboard.Key, button, None) or keyboard.KeyCode.from_char(button)
            kb_ctrl.press(k)
            if duration > 0:
                time.sleep(duration / 1000)
                kb_ctrl.release(k)
        except: pass
    elif action == 'release_key':
        try:
            k = getattr(keyboard.Key, button, None) or keyboard.KeyCode.from_char(button)
            kb_ctrl.release(k)
        except: pass
    elif action == 'wait':
        time.sleep(duration / 1000)
    if delay_after > 0:
        time.sleep(delay_after / 1000)

def save_macro():
    if not macro_steps:
        messagebox.showwarning("Сохранение", "Нет шагов для сохранения!")
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Macro файл", "*.json"), ("Все файлы", "*.*")],
        title="Сохранить макрос"
    )
    if not path: return
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'repeat': macro_repeat_var.get(), 'steps': macro_steps}, f, ensure_ascii=False, indent=2)
    messagebox.showinfo("Сохранено", f"Макрос сохранён:\n{path}")

def load_macro():
    path = filedialog.askopenfilename(
        filetypes=[("Macro файл", "*.json"), ("Все файлы", "*.*")],
        title="Загрузить макрос"
    )
    if not path: return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        macro_steps.clear()
        macro_steps.extend(data.get('steps', []))
        macro_repeat_var.set(data.get('repeat', 0))
        refresh_steps()
        messagebox.showinfo("Загружено", f"Макрос загружен:\n{os.path.basename(path)}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить:\n{e}")

def add_step(): open_step_editor(None)
def edit_step(i): open_step_editor(i)
def delete_step(i):
    macro_steps.pop(i); refresh_steps()

def open_step_editor(index):
    global macro_recording_target
    data = macro_steps[index] if index is not None else {
        'action': 'hold_mouse', 'button': 'MOUSE1', 'duration': 500, 'delay_after': 0
    }
    win = tk.Toplevel(root)
    win.title("Редактор шага")
    win.geometry("340x300")
    win.configure(bg="#0f172a")
    win.resizable(False, False)
    win.grab_set()

    lf = tkfont.Font(family="Segoe UI", size=10)
    bf = tkfont.Font(family="Segoe UI", size=10, weight="bold")

    tk.Label(win, text="Действие:", font=lf, bg="#0f172a", fg="#94a3b8").pack(anchor='w', padx=20, pady=(16,2))
    action_var = tk.StringVar(value=data['action'])
    ttk.Combobox(win, textvariable=action_var, state="readonly", width=30,
                 values=["hold_mouse","release_mouse","hold_key","release_key","wait"]
                 ).pack(padx=20, fill='x')

    tk.Label(win, text="Кнопка / Клавиша:", font=lf, bg="#0f172a", fg="#94a3b8").pack(anchor='w', padx=20, pady=(10,2))
    btn_frame = tk.Frame(win, bg="#0f172a"); btn_frame.pack(padx=20, fill='x')
    btn_var = tk.StringVar(value=data.get('button','MOUSE1'))
    tk.Entry(btn_frame, textvariable=btn_var, font=lf,
             bg="#1e293b", fg="white", insertbackground="white", width=18).pack(side='left')

    rec_btn_ref = [None]

    def start_step_record():
        global macro_recording_target
        macro_recording_target = 'step_x'
        rec_btn_ref[0].config(text="Нажми...", state="disabled")

        def cb_mouse(b):
            global macro_recording_target
            macro_recording_target = None
            btn_var.set(MOUSE_BUTTON_NAMES.get(b, str(b)))
            rec_btn_ref[0].config(text="Записать", state="normal")

        def cb_key(key):
            global macro_recording_target
            if macro_recording_target != 'step_x': return
            macro_recording_target = None
            name = key.char if hasattr(key,'char') and key.char else str(key).replace('Key.','')
            btn_var.set(name)
            rec_btn_ref[0].config(text="Записать", state="normal")
            tmp_kb.stop()

        tmp_kb = keyboard.Listener(on_press=cb_key); tmp_kb.daemon=True; tmp_kb.start()

        def ms_cb(x, y, button, pressed):
            if macro_recording_target != 'step_x': return
            if pressed and button != Button.left:
                root.after(0, lambda b=button: cb_mouse(b))
                return False
        tmp_ms = mouse.Listener(on_click=ms_cb); tmp_ms.daemon=True; tmp_ms.start()

    rec_btn = tk.Button(btn_frame, text="Записать", font=lf, bg="#1e40af", fg="white",
                        relief="flat", padx=8, command=start_step_record)
    rec_btn.pack(side='left', padx=(8,0))
    rec_btn_ref[0] = rec_btn

    tk.Label(win, text="Длительность зажатия (мс):", font=lf, bg="#0f172a", fg="#94a3b8").pack(anchor='w', padx=20, pady=(10,2))
    dur_var = tk.IntVar(value=data.get('duration',500))
    tk.Entry(win, textvariable=dur_var, font=lf, bg="#1e293b", fg="white",
             insertbackground="white", width=10).pack(padx=20, anchor='w')

    tk.Label(win, text="Задержка после (мс):", font=lf, bg="#0f172a", fg="#94a3b8").pack(anchor='w', padx=20, pady=(8,2))
    delay_var = tk.IntVar(value=data.get('delay_after',0))
    tk.Entry(win, textvariable=delay_var, font=lf, bg="#1e293b", fg="white",
             insertbackground="white", width=10).pack(padx=20, anchor='w')

    def save():
        global macro_recording_target
        macro_recording_target = None
        step = {'action': action_var.get(), 'button': btn_var.get(),
                'duration': dur_var.get(), 'delay_after': delay_var.get()}
        if index is None: macro_steps.append(step)
        else: macro_steps[index] = step
        refresh_steps(); win.destroy()

    tk.Button(win, text="Сохранить шаг", font=bf, bg="#16a34a", fg="white",
              activebackground="#15803d", relief="flat", padx=16, pady=6,
              command=save).pack(pady=(14,0))

def refresh_steps():
    for w in steps_frame.winfo_children(): w.destroy()
    lf = tkfont.Font(family="Segoe UI", size=9)
    LABELS = {'hold_mouse':'🖱 Зажать','release_mouse':'🖱 Отпустить',
              'hold_key':'⌨ Зажать','release_key':'⌨ Отпустить','wait':'⏱ Ждать'}
    for i, step in enumerate(macro_steps):
        row = tk.Frame(steps_frame, bg="#1e293b", pady=4); row.pack(fill='x', padx=4, pady=2)
        lbl = LABELS.get(step['action'], step['action'])
        text = f"{i+1}. {lbl} {step.get('button','')}  |  {step.get('duration',0)}мс  +  {step.get('delay_after',0)}мс"
        tk.Label(row, text=text, font=lf, bg="#1e293b", fg="#e2e8f0", anchor='w').pack(side='left', padx=8)
        tk.Button(row, text="✏", font=lf, bg="#1e293b", fg="#38bdf8", relief="flat",
                  command=lambda idx=i: edit_step(idx)).pack(side='right', padx=2)
        tk.Button(row, text="✕", font=lf, bg="#1e293b", fg="#f87171", relief="flat",
                  command=lambda idx=i: delete_step(idx)).pack(side='right', padx=2)

def set_macro_hotkey_mouse(button):
    global macro_hotkey, macro_hotkey_type, macro_recording_target
    macro_recording_target = None
    macro_hotkey = button; macro_hotkey_type = 'mouse'
    macro_hotkey_label.config(text=f"[ {MOUSE_BUTTON_NAMES.get(button, str(button))} ]")
    macro_hotkey_btn.config(text="Назначить", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")

def start_macro_hotkey_record():
    global macro_recording_target
    macro_recording_target = 'hotkey'
    macro_hotkey_btn.config(text="Нажми...", bg="#1e3a5f", state="disabled")
    macro_hotkey_label.config(text="—")
    root.focus_force()
    root.bind("<KeyPress>", capture_macro_hotkey_key)

def capture_macro_hotkey_key(event):
    global macro_hotkey, macro_hotkey_type, macro_recording_target
    if macro_recording_target != 'hotkey': return
    macro_recording_target = None
    mapped = map_keysym(event.keysym)
    if mapped:
        macro_hotkey = mapped[0]; macro_hotkey_type = 'keyboard'
        macro_hotkey_label.config(text=f"[ {mapped[1]} ]")
    macro_hotkey_btn.config(text="Назначить", bg="#1e40af", state="normal")
    root.unbind("<KeyPress>")

def show_instructions():
    win = tk.Toplevel(root)
    win.title("Инструкция")
    win.geometry("480x440")
    win.configure(bg="#0f172a")
    win.resizable(False, False)
    lf = tkfont.Font(family="Segoe UI", size=10)
    tf = tkfont.Font(family="Segoe UI", size=13, weight="bold")
    tk.Label(win, text="📖 Инструкция по эксплуатации", font=tf,
             bg="#0f172a", fg="#e2e8f0").pack(pady=(16,4))
    tk.Label(win, text="by J.O.T.V.N  |  Никита Жирный Качёк Грелд", font=lf,
             bg="#0f172a", fg="#f59e0b").pack(pady=(0,12))
    text = tk.Text(win, font=lf, bg="#0f172a", fg="#94a3b8", relief="flat",
                   wrap="word", padx=20, pady=10)
    text.pack(fill='both', expand=True, padx=10)
    instructions = """🎮 ВКЛАДКА «ПЕРЕКЛЮЧАТЕЛЬ»
Устал зажимать кнопку во время рыбалки или гринда?

1. «Что зажимать» — выбери кнопку мыши или клавишу которую нужно держать зажатой (MOUSE1, MOUSE2, MOUSE3, MOUSE4, MOUSE5 или любая клавиша).
2. «Хоткей» — назначь клавишу/кнопку которой будешь переключать зажатие.
Одно нажатие хоткея — зажато. Ещё раз — отпущено.

⚙️ ВКЛАДКА «МАКРО-РЕДАКТОР»
Создавай последовательности действий:
  • hold_mouse    — зажать кнопку мыши на N мс
  • release_mouse — отпустить кнопку мыши
  • hold_key      — зажать клавишу на N мс
  • release_key   — отпустить клавишу
  • wait          — просто подождать N мс

Повторений: 0 = бесконечный цикл.

💾 СОХРАНЕНИЕ И ЗАГРУЗКА
Макрос сохраняется в .json — храни профили под разные игры.

🔥 Специально для тех кто заебался от тупого гринда скилов в играх вроде Ashes and Blood. Твоя мышь, клава и палец скажут спасибо.

Приложение создано J.O.T.V.N — всё очень просто."""
    text.insert("1.0", instructions)
    text.config(state="disabled")

def map_keysym(key_name):
    special_map = {
        "F1":keyboard.Key.f1,"F2":keyboard.Key.f2,"F3":keyboard.Key.f3,
        "F4":keyboard.Key.f4,"F5":keyboard.Key.f5,"F6":keyboard.Key.f6,
        "F7":keyboard.Key.f7,"F8":keyboard.Key.f8,"F9":keyboard.Key.f9,
        "F10":keyboard.Key.f10,"F11":keyboard.Key.f11,"F12":keyboard.Key.f12,
        "Insert":keyboard.Key.insert,"Delete":keyboard.Key.delete,
        "Home":keyboard.Key.home,"End":keyboard.Key.end,
        "Prior":keyboard.Key.page_up,"Next":keyboard.Key.page_down,
        "Caps_Lock":keyboard.Key.caps_lock,"Tab":keyboard.Key.tab,
        "BackSpace":keyboard.Key.backspace,"Return":keyboard.Key.enter,
        "Escape":keyboard.Key.esc,"space":keyboard.Key.space,
        "Up":keyboard.Key.up,"Down":keyboard.Key.down,
        "Left":keyboard.Key.left,"Right":keyboard.Key.right,
    }
    if key_name in special_map: return (special_map[key_name], key_name)
    if len(key_name) == 1: return (keyboard.KeyCode.from_char(key_name.lower()), key_name.upper())
    return None

def on_close():
    if holding: release_target()
    for l in [kb_listener, ms_listener]:
        if l:
            try: l.stop()
            except: pass
    root.destroy()

# ══════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════

root = tk.Tk()
root.title("AutoClick Toggle — J.O.T.V.N")
root.geometry("440x580")
root.resizable(False, False)
root.configure(bg="#0f172a")
root.protocol("WM_DELETE_WINDOW", on_close)

title_f  = tkfont.Font(family="Segoe UI", size=14, weight="bold")
sub_f    = tkfont.Font(family="Segoe UI", size=8,  weight="bold")
label_f  = tkfont.Font(family="Segoe UI", size=10)
key_f    = tkfont.Font(family="Consolas", size=13, weight="bold")
status_f = tkfont.Font(family="Segoe UI", size=12, weight="bold")
bold_f   = tkfont.Font(family="Segoe UI", size=10, weight="bold")
tiny_f   = tkfont.Font(family="Segoe UI", size=8)

header = tk.Frame(root, bg="#0f172a")
header.pack(fill='x', padx=20, pady=(14,0))
tk.Label(header, text="AutoClick Toggle", font=title_f, bg="#0f172a", fg="#e2e8f0").pack(side='left')
tk.Button(header, text="❓ Инструкция", font=tiny_f, bg="#1e293b", fg="#94a3b8",
          relief="flat", padx=8, pady=4, cursor="hand2",
          command=show_instructions).pack(side='right')

tk.Label(root, text="Заебался от тупого гринда? Твой палец в ахуе? — это для тебя.",
         font=tiny_f, bg="#0f172a", fg="#64748b").pack()
tk.Label(root, text="Никита Жирный Качёк Грелд  |  J.O.T.V.N",
         font=sub_f, bg="#0f172a", fg="#f59e0b").pack(pady=(2,8))

tab_frame = tk.Frame(root, bg="#0f172a")
tab_frame.pack(fill='x', padx=20)
tab_toggle_btn = tk.Button(tab_frame, text="Переключатель", font=bold_f,
                           bg="#1e40af", fg="white", relief="flat", padx=12, pady=6)
tab_macro_btn  = tk.Button(tab_frame, text="Макро-редактор", font=bold_f,
                           bg="#1e293b", fg="#94a3b8", relief="flat", padx=12, pady=6)
tab_toggle_btn.pack(side='left')
tab_macro_btn.pack(side='left', padx=(4,0))

content = tk.Frame(root, bg="#0f172a")
content.pack(fill='both', expand=True, padx=20, pady=8)

# ── Toggle page ───────────────────────────────────────────────
toggle_page = tk.Frame(content, bg="#0f172a")

# Что зажимать
tk.Label(toggle_page, text="Что зажимать:", font=bold_f, bg="#0f172a", fg="#e2e8f0").pack(anchor='w', pady=(12,4))
target_row = tk.Frame(toggle_page, bg="#0f172a"); target_row.pack(fill='x')
toggle_target_label = tk.Label(target_row, text="[ MOUSE1 (ЛКМ) ]", font=key_f, bg="#0f172a", fg="#a78bfa")
toggle_target_label.pack(side='left')
toggle_target_btn = tk.Button(target_row, text="Назначить", font=label_f,
                              bg="#7c3aed", fg="white", activebackground="#4c1d95",
                              relief="flat", padx=12, pady=6, cursor="hand2",
                              command=start_target_recording)
toggle_target_btn.pack(side='left', padx=(12,0))

tk.Frame(toggle_page, bg="#1e293b", height=1).pack(fill='x', pady=12)

# Хоткей
tk.Label(toggle_page, text="Хоткей (переключатель):", font=bold_f, bg="#0f172a", fg="#e2e8f0").pack(anchor='w', pady=(0,4))
hotkey_row = tk.Frame(toggle_page, bg="#0f172a"); hotkey_row.pack(fill='x')
toggle_hotkey_label = tk.Label(hotkey_row, text="—", font=key_f, bg="#0f172a", fg="#38bdf8")
toggle_hotkey_label.pack(side='left')
toggle_record_btn = tk.Button(hotkey_row, text="Назначить", font=label_f,
                              bg="#1e40af", fg="white", activebackground="#1e3a8a",
                              relief="flat", padx=12, pady=6, cursor="hand2",
                              command=start_toggle_recording)
toggle_record_btn.pack(side='left', padx=(12,0))

tk.Frame(toggle_page, bg="#1e293b", height=1).pack(fill='x', pady=16)

toggle_status = tk.Label(toggle_page, text="🔴 Отпущено", font=status_f,
                         bg="#0f172a", fg="#f87171")
toggle_status.pack()

# ── Macro page ────────────────────────────────────────────────
macro_page = tk.Frame(content, bg="#0f172a")

hk_row = tk.Frame(macro_page, bg="#0f172a"); hk_row.pack(fill='x', pady=(8,4))
tk.Label(hk_row, text="Хоткей:", font=label_f, bg="#0f172a", fg="#94a3b8").pack(side='left')
macro_hotkey_label = tk.Label(hk_row, text="—", font=key_f, bg="#0f172a", fg="#38bdf8")
macro_hotkey_label.pack(side='left', padx=8)
macro_hotkey_btn = tk.Button(hk_row, text="Назначить", font=label_f,
                             bg="#1e40af", fg="white", relief="flat", padx=8, pady=4,
                             command=start_macro_hotkey_record)
macro_hotkey_btn.pack(side='left')

rep_row = tk.Frame(macro_page, bg="#0f172a"); rep_row.pack(fill='x', pady=4)
tk.Label(rep_row, text="Повторений (0=∞):", font=label_f, bg="#0f172a", fg="#94a3b8").pack(side='left')
macro_repeat_var = tk.IntVar(value=0)
tk.Entry(rep_row, textvariable=macro_repeat_var, font=label_f,
         bg="#1e293b", fg="white", insertbackground="white", width=6).pack(side='left', padx=8)

sl_row = tk.Frame(macro_page, bg="#0f172a"); sl_row.pack(fill='x', pady=(4,2))
tk.Button(sl_row, text="💾 Сохранить", font=label_f, bg="#0f4c81", fg="white",
          relief="flat", padx=10, pady=4, cursor="hand2",
          command=save_macro).pack(side='left')
tk.Button(sl_row, text="📂 Загрузить", font=label_f, bg="#1e293b", fg="#38bdf8",
          relief="flat", padx=10, pady=4, cursor="hand2",
          command=load_macro).pack(side='left', padx=(8,0))

tk.Label(macro_page, text="Шаги:", font=bold_f, bg="#0f172a", fg="#e2e8f0").pack(anchor='w', pady=(8,2))
steps_canvas = tk.Canvas(macro_page, bg="#0f172a", highlightthickness=0, height=160)
steps_canvas.pack(fill='x')
steps_frame = tk.Frame(steps_canvas, bg="#0f172a")
steps_canvas.create_window((0,0), window=steps_frame, anchor='nw')
steps_frame.bind("<Configure>", lambda e: steps_canvas.configure(scrollregion=steps_canvas.bbox("all")))

tk.Button(macro_page, text="+ Добавить шаг", font=label_f,
          bg="#0f172a", fg="#38bdf8", relief="flat", cursor="hand2",
          command=add_step).pack(anchor='w', pady=(4,8))

run_row = tk.Frame(macro_page, bg="#0f172a"); run_row.pack(fill='x')
macro_run_btn = tk.Button(run_row, text="▶ Запустить", font=bold_f,
                          bg="#16a34a", fg="white", activebackground="#15803d",
                          relief="flat", padx=16, pady=8, command=toggle_macro)
macro_run_btn.pack(side='left')
macro_status = tk.Label(run_row, text="⏹ Остановлено", font=status_f,
                        bg="#0f172a", fg="#94a3b8")
macro_status.pack(side='left', padx=12)

def show_toggle():
    macro_page.pack_forget()
    toggle_page.pack(fill='both', expand=True)
    tab_toggle_btn.config(bg="#1e40af", fg="white")
    tab_macro_btn.config(bg="#1e293b", fg="#94a3b8")

def show_macro():
    toggle_page.pack_forget()
    macro_page.pack(fill='both', expand=True)
    tab_macro_btn.config(bg="#1e40af", fg="white")
    tab_toggle_btn.config(bg="#1e293b", fg="#94a3b8")

tab_toggle_btn.config(command=show_toggle)
tab_macro_btn.config(command=show_macro)
show_toggle()

# default hold target = LMB
hold_target = ('mouse', Button.left)

start_listeners()
root.mainloop()
