# app.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, Menu, ttk, scrolledtext
from PIL import Image, ImageTk
import webbrowser
import hashlib
import secrets
import os
import json
import logging
import random
import string
from datetime import datetime

# Импорты вашей логики
from connect import (
    Avtorization, Motivation, Affirmation, FunnyQuote, 
    AdminRequests, UserBan, AdminActionLog, 
    UserReaction, BanAppeal, init_db 
)
from ban_manager import BanManager

# ========== КОНФИГУРАЦИЯ САМУРАЙСКОГО СТИЛЯ ==========
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Цветовая палитра самурайской темы
SAMURAI_BG = "#0d0d0d"           
SAMURAI_PANEL = "#1a1a1a"        
SAMURAI_CARD = "#262626"         
SAMURAI_RED = "#8B0000"          
SAMURAI_RED_HOVER = "#5e0000"    
SAMURAI_GOLD = "#D4AF37"         
SAMURAI_GOLD_HOVER = "#b08d2b"   
SAMURAI_TEXT = "#E8E8E8"         
SAMURAI_TEXT_SECONDARY = "#A0A0A0"  
SAMURAI_GREEN = "#2E8B57"        
SAMURAI_GREEN_HOVER = "#3e6b3f"  

# Настройка шрифтов
FONT_PRIMARY = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 12, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_HEADER = ("Segoe UI", 16, "bold")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_errors.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Глобальные переменные
current_user = None
active_windows = {}

# Инициализация корневого окна
root = ctk.CTk()
root.title('Bushido Motivation System')
root.geometry('1280x800')
root.configure(fg_color=SAMURAI_BG)

# Настройка стилей для ttk виджетов (Treeview и т.д.)
style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", 
                background=SAMURAI_CARD,
                fieldbackground=SAMURAI_CARD,
                foreground=SAMURAI_TEXT,
                borderwidth=0,
                rowheight=25)
style.configure("Treeview.Heading", 
                background=SAMURAI_RED,
                foreground="white",
                relief="flat",
                font=('Segoe UI', 10, 'bold'))
style.map("Treeview", 
          background=[('selected', SAMURAI_GOLD)],
          foreground=[('selected', 'black')])

# Менеджер банов
ban_manager = BanManager()

# Переменные анимации
loading_window = None
loading_progress = None
loading_label = None
loading_canvas = None
loading_frames = []
loading_animation_id = None

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ СТИЛЯ ==========

def create_samurai_button(parent, text, command=None, color=SAMURAI_RED, hover_color=SAMURAI_RED_HOVER, 
                         text_color="white", width=140, height=35, font=FONT_BOLD):
    return ctk.CTkButton(
        parent, text=text, command=command, fg_color=color, hover_color=hover_color,
        text_color=text_color, corner_radius=0, border_width=1, border_color=SAMURAI_GOLD,
        font=font, width=width, height=height
    )

def create_samurai_entry(parent, placeholder="", show=None, width=300):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder, show=show, fg_color=SAMURAI_PANEL,
        border_color=SAMURAI_GOLD, text_color=SAMURAI_TEXT, corner_radius=0,
        height=35, width=width, font=FONT_PRIMARY
    )

def create_scrollable_textbox(parent, height=100, width=600):
    """Создает скроллируемое текстовое поле с кастомным скроллбаром"""
    # Используем CTkTextbox для лучшей совместимости и работающего скроллбара
    return ctk.CTkTextbox(
        parent, 
        fg_color=SAMURAI_PANEL, 
        border_color=SAMURAI_GOLD,
        text_color=SAMURAI_TEXT, 
        corner_radius=0, 
        height=height,
        width=width, 
        font=FONT_PRIMARY, 
        border_width=1,
        scrollbar_button_color=SAMURAI_RED,
        scrollbar_button_hover_color=SAMURAI_RED_HOVER
    )

def create_samurai_textbox(parent, height=100, width=600, scrollable=False):
    """Создает текстовое поле с возможностью скролла"""
    return ctk.CTkTextbox(
        parent, 
        fg_color=SAMURAI_PANEL, 
        border_color=SAMURAI_GOLD,
        text_color=SAMURAI_TEXT, 
        corner_radius=0, 
        height=height,
        width=width, 
        font=FONT_PRIMARY, 
        border_width=1,
        scrollbar_button_color=SAMURAI_RED,
        scrollbar_button_hover_color=SAMURAI_RED_HOVER
    )

def create_samurai_label(parent, text, font=FONT_PRIMARY, text_color=SAMURAI_TEXT, **kwargs):
    return ctk.CTkLabel(parent, text=text, font=font, text_color=text_color, **kwargs)

def create_samurai_frame(parent, fg_color=SAMURAI_PANEL, border_color=None, **kwargs):
    if border_color:
        return ctk.CTkFrame(parent, fg_color=fg_color, border_color=border_color, border_width=2, corner_radius=0, **kwargs)
    return ctk.CTkFrame(parent, fg_color=fg_color, corner_radius=0, **kwargs)

def create_samurai_progressbar(parent, width=300):
    return ctk.CTkProgressBar(parent, width=width, height=15, progress_color=SAMURAI_RED, fg_color=SAMURAI_PANEL, corner_radius=0)

# --- ФУНКЦИЯ ДЛЯ СКРОЛЛИНГА TREEVIEW ---
def setup_touchpad_scrolling(widget):
    """Включает прокрутку тачпадом для ttk виджетов"""
    def _on_mousewheel(event):
        try:
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception: pass

    def _on_linux_scroll_up(event):
        widget.yview_scroll(-1, "units")

    def _on_linux_scroll_down(event):
        widget.yview_scroll(1, "units")

    def _bind_to_mousewheel(event):
        widget.bind_all("<MouseWheel>", _on_mousewheel)
        widget.bind_all("<Button-4>", _on_linux_scroll_up)
        widget.bind_all("<Button-5>", _on_linux_scroll_down)

    def _unbind_from_mousewheel(event):
        widget.unbind_all("<MouseWheel>")
        widget.unbind_all("<Button-4>")
        widget.unbind_all("<Button-5>")

    widget.bind('<Enter>', _bind_to_mousewheel)
    widget.bind('<Leave>', _unbind_from_mousewheel)

# ========== ФУНКЦИОНАЛЬНЫЕ ФУНКЦИИ ==========

def generate_captcha_text():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

def draw_captcha(canvas, text):
    canvas.delete("all")
    w, h = 150, 50
    canvas.create_rectangle(0, 0, w, h, fill=SAMURAI_PANEL, outline=SAMURAI_GOLD, width=1)
    for i in range(30):
        x1, y1 = random.randint(0, w), random.randint(0, h)
        x2, y2 = random.randint(0, w), random.randint(0, h)
        canvas.create_line(x1, y1, x2, y2, fill='#444', width=1)
    canvas.create_text(75, 25, text=text, font=('Arial', 24, 'bold', 'italic'), fill=SAMURAI_GOLD)
    for i in range(150):
        x, y = random.randint(0, w), random.randint(0, h)
        canvas.create_oval(x, y, x+1, y+1, fill='#555')

def safe_execute(func, *args, **kwargs):
    try: return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Ошибка в функции {func.__name__}: {str(e)}")
        return None

def safe_widget_update(widget, method, *args, **kwargs):
    try:
        if hasattr(widget, method) and widget.winfo_exists():
            getattr(widget, method)(*args, **kwargs)
            return True
    except Exception as e: logger.warning(f"Не удалось обновить виджет {widget}: {str(e)}")
    return False

# ========== ФУНКЦИИ АВТОРИЗАЦИИ И БЕЗОПАСНОСТИ ==========

def hash_password(password): 
    return hashlib.sha256(password.encode()).hexdigest()

def generate_admin_token(): 
    return secrets.token_urlsafe(16)

def save_token_to_file(username, token):
    if not os.path.exists('tokens'): 
        os.makedirs('tokens')
    filename = f"tokens/{username}_token.txt"
    with open(filename, 'w') as f: 
        f.write(token)
    return filename

def get_current_user_token():
    global current_user
    if current_user is None: 
        return None
    token_filename = f"tokens/{current_user['username']}_token.txt"
    if os.path.exists(token_filename):
        with open(token_filename, 'r') as f: 
            return f.read().strip()
    return None

def is_main_admin():
    global current_user
    if current_user is None: 
        return False
    try:
        user = Avtorization.get(Avtorization.username == current_user['username'])
        return user.is_main_admin and user.role == 'администратор'
    except Avtorization.DoesNotExist: 
        return False

def is_user_admin(username):
    try:
        user = Avtorization.get(Avtorization.username == username)
        return user.role == 'администратор'
    except Avtorization.DoesNotExist: 
        return False

def has_pending_admin_request(username):
    try:
        AdminRequests.get((AdminRequests.username == username) & (AdminRequests.status == 'ожидание'))
        return True
    except AdminRequests.DoesNotExist: 
        return False

def is_user_banned(username): 
    return ban_manager.is_banned(username)

def can_ban_user(target_username):
    global current_user
    if current_user is None: 
        return False
    if target_username == current_user['username']: 
        return False
    try:
        target_user = Avtorization.get(Avtorization.username == target_username)
        current_user_obj = Avtorization.get(Avtorization.username == current_user['username'])
        if current_user_obj.is_main_admin: 
            return True
        if current_user_obj.role == 'администратор' and target_user.role == 'пользователь': 
            return True
        return False
    except Avtorization.DoesNotExist: 
        return False

def can_unban_user(username):
    global current_user
    if current_user is None: 
        return False
    if is_main_admin(): 
        return True
    try:
        ban_info = UserBan.get(UserBan.username == username, UserBan.is_active == True)
        return ban_info.banned_by == current_user['username']
    except UserBan.DoesNotExist: 
        return False

def ban_user(username, reason=""):
    global current_user
    if current_user is None: 
        return {"status": "error", "message": "Не авторизован"}
    if not can_ban_user(username): 
        return {"status": "error", "message": "Недостаточно прав для изгнания этого воина"}
    banned_by = current_user['username']
    success, message = ban_manager.ban_user(username, banned_by, reason)
    return {"status": "success" if success else "error", "message": message}

def unban_user(username):
    global current_user
    if current_user is None: 
        return {"status": "error", "message": "Не авторизован"}
    unbanned_by = current_user['username']
    try:
        ban_info = UserBan.get(UserBan.username == username, UserBan.is_active == True)
        if not can_unban_user(username): 
            return {"status": "error", "message": "Только изгнавший Сёгун или Главный Сёгун может вернуть путь"}
        success, message = ban_manager.unban_user(username, unbanned_by)
        return {"status": "success" if success else "error", "message": message}
    except UserBan.DoesNotExist: 
        return {"status": "error", "message": "Воин не изгнан или не найден"}

def check_auth():
    global current_user
    if current_user is None:
        show_auth_window()
        return False
    if is_user_banned(current_user['username']):
        messagebox.showerror("Изгнание", "Ваш путь закрыт. Обратитесь к сёгуну.")
        logout()
        return False
    return True

# ========== АНИМАЦИЯ ЗАГРУЗКИ ==========

def load_gif_frames():
    global loading_frames
    loading_frames = []
    gif_path = "content/upload.gif"
    try:
        if os.path.exists(gif_path):
            gif = Image.open(gif_path)
            for frame in range(gif.n_frames):
                gif.seek(frame)
                frame_image = gif.copy().resize((200, 150), Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=frame_image, dark_image=frame_image, size=(200, 150))
                loading_frames.append(ctk_image)
    except Exception as e: 
        logger.error(f"Ошибка загрузки GIF: {e}")

def show_loading_screen(target_function, *args):
    global loading_window, loading_progress, loading_label, loading_canvas, loading_animation_id
    
    if not loading_frames:
        load_gif_frames()

    loading_window = ctk.CTkToplevel(root)
    loading_window.title("")
    loading_window.geometry("400x350")
    loading_window.overrideredirect(True)
    loading_window.configure(fg_color=SAMURAI_BG)
    loading_window.attributes('-topmost', True)
    
    # Центрирование
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - 200
    y = root.winfo_y() + (root.winfo_height() // 2) - 175
    loading_window.geometry(f"+{x}+{y}")
    loading_window.transient(root)
    loading_window.grab_set()
    
    # Основной контейнер с рамкой
    border_frame = create_samurai_frame(loading_window, border_color=SAMURAI_GOLD)
    border_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    create_samurai_label(border_frame, "Медитация...", font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=(25, 10))
    
    # Контейнер для анимации
    animation_frame = create_samurai_frame(border_frame, fg_color=SAMURAI_BG)
    animation_frame.pack(pady=5)
    
    # Для CTkImage используем CTkLabel
    animation_label = ctk.CTkLabel(animation_frame, text="", fg_color=SAMURAI_BG)
    animation_label.pack()
    
    # Прогресс-бар
    loading_progress = create_samurai_progressbar(border_frame)
    loading_progress.set(0)
    loading_progress.pack(pady=15)
    
    loading_label = create_samurai_label(border_frame, "0%", text_color=SAMURAI_TEXT_SECONDARY)
    loading_label.pack(pady=5)

    current_frame_index = 0
    progress_value = 0
    
    def play_animation():
        nonlocal current_frame_index, progress_value
        
        if not loading_window or not loading_window.winfo_exists():
            return

        # Обновление кадра GIF
        if loading_frames and current_frame_index < len(loading_frames):
            animation_label.configure(image=loading_frames[current_frame_index])
            current_frame_index = (current_frame_index + 1) % len(loading_frames)
        
        # Обновление прогресса
        if progress_value < 100:
            progress_value += 2
            loading_progress.set(progress_value / 100)
            loading_label.configure(text=f"Подготовка додзё... {progress_value}%")
            
            global loading_animation_id
            loading_animation_id = loading_window.after(30, play_animation)
        else:
            if loading_animation_id:
                try:
                    loading_window.after_cancel(loading_animation_id)
                except:
                    pass
            
            loading_window.destroy()
            root.after(50, lambda: target_function(*args))

    play_animation()

# ========== ОКНО АВТОРИЗАЦИИ ==========

def show_auth_window():
    # Создаем первого администратора при необходимости
    create_first_admin()
    
    for widget in root.winfo_children():
        widget.destroy()
    
    # Главный контейнер
    main_frame = create_samurai_frame(root, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True)
    
    # Заголовок
    title_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    title_frame.pack(pady=50)
    
    create_samurai_label(title_frame, "Путь Самурая", font=FONT_TITLE, text_color=SAMURAI_GOLD).pack()
    create_samurai_label(title_frame, "Система мотивационных высказываний", 
                        font=FONT_PRIMARY, text_color=SAMURAI_TEXT_SECONDARY).pack(pady=10)
    
    # Контейнер для форм
    form_container = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    form_container.pack(pady=20)
    
    show_login_form(form_container)

def show_login_form(parent):
    # Очищаем контейнер
    for widget in parent.winfo_children():
        widget.destroy()
    
    # Форма входа
    login_frame = create_samurai_frame(parent, border_color=SAMURAI_GOLD)
    login_frame.pack(padx=50, pady=20)
    
    create_samurai_label(login_frame, "Вход в Додзё", font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=20)
    
    # Поля ввода
    input_frame = create_samurai_frame(login_frame, fg_color=SAMURAI_BG)
    input_frame.pack(padx=30, pady=10, fill='x')
    
    create_samurai_label(input_frame, "Имя воина", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    username_entry = create_samurai_entry(input_frame, "Введите имя")
    username_entry.pack(fill='x', pady=5)
    
    create_samurai_label(input_frame, "Секретный свиток", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    password_entry = create_samurai_entry(input_frame, "Введите пароль", show="*")
    password_entry.pack(fill='x', pady=5)
    
    # Капча
    captcha_frame = create_samurai_frame(login_frame, fg_color=SAMURAI_BG)
    captcha_frame.pack(pady=10)
    
    captcha_val = generate_captcha_text()
    
    captcha_canvas = tk.Canvas(captcha_frame, width=150, height=50, bg=SAMURAI_BG, highlightthickness=0)
    captcha_canvas.pack()
    draw_captcha(captcha_canvas, captcha_val)
    
    captcha_input_frame = create_samurai_frame(login_frame, fg_color=SAMURAI_BG)
    captcha_input_frame.pack(pady=5)
    
    create_samurai_label(captcha_input_frame, "Введите код с картинки:", 
                        text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 10)).pack()
    
    captcha_entry_frame = create_samurai_frame(captcha_input_frame, fg_color=SAMURAI_BG)
    captcha_entry_frame.pack(pady=5)
    
    captcha_entry = create_samurai_entry(captcha_entry_frame, width=100)
    captcha_entry.pack(side='left', padx=5)
    
    def refresh_captcha():
        nonlocal captcha_val
        captcha_val = generate_captcha_text()
        draw_captcha(captcha_canvas, captcha_val)
        captcha_entry.delete(0, 'end')
    
    create_samurai_button(captcha_entry_frame, "↻", refresh_captcha, width=40).pack(side='left', padx=5)
    
    def login():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        captcha_input = captcha_entry.get().strip().upper()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        if captcha_input != captcha_val:
            messagebox.showerror("Ошибка", "Неверный код подтверждения")
            refresh_captcha()
            return
        
        # Проверка бана
        if is_user_banned(username):
            if messagebox.askyesno("Изгнание", "Ваш путь закрыт. Хотите написать прошение сёгуну?"):
                show_ban_appeal_window(username)
            return
        
        try:
            user = Avtorization.get(Avtorization.username == username)
            if user.password == hash_password(password):
                global current_user
                current_user = {
                    'username': user.username,
                    'role': user.role
                }
                
                # Проверяем заявку на администрирование
                try:
                    approved_request = AdminRequests.get(
                        (AdminRequests.username == username) & 
                        (AdminRequests.status == 'одобрено')
                    )
                    if user.role != 'администратор':
                        messagebox.showinfo("Заявка одобрена", "Ваше прошение принято! Завершите посвящение.")
                        complete_admin_registration_window(username)
                        return
                except AdminRequests.DoesNotExist:
                    pass
                
                home_window()
            else:
                messagebox.showerror("Ошибка", "Неверный пароль")
                refresh_captcha()
        except Avtorization.DoesNotExist:
            messagebox.showerror("Ошибка", "Воин не найден")
            refresh_captcha()
    
    create_samurai_button(login_frame, "Войти", login).pack(pady=20)
    
    # Ссылка на регистрацию
    def switch_to_register():
        show_register_form(parent)
    
    register_link = create_samurai_label(login_frame, "Нет пути? Создать новый", 
                                       text_color=SAMURAI_GOLD, font=('Segoe UI', 10, 'underline'))
    register_link.pack(pady=10)
    register_link.bind("<Button-1>", lambda e: switch_to_register())

def show_register_form(parent):
    # Очищаем контейнер
    for widget in parent.winfo_children():
        widget.destroy()
    
    # Форма регистрации
    register_frame = create_samurai_frame(parent, border_color=SAMURAI_GOLD)
    register_frame.pack(padx=50, pady=20)
    
    create_samurai_label(register_frame, "Новый путь", font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=20)
    
    # Поля ввода
    input_frame = create_samurai_frame(register_frame, fg_color=SAMURAI_BG)
    input_frame.pack(padx=30, pady=10, fill='x')
    
    create_samurai_label(input_frame, "Имя воина", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    username_entry = create_samurai_entry(input_frame, "Введите имя")
    username_entry.pack(fill='x', pady=5)
    
    create_samurai_label(input_frame, "Секретный свиток", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    password_entry = create_samurai_entry(input_frame, "Введите пароль", show="*")
    password_entry.pack(fill='x', pady=5)
    
    create_samurai_label(input_frame, "Подтверждение свитка", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    confirm_entry = create_samurai_entry(input_frame, "Повторите пароль", show="*")
    confirm_entry.pack(fill='x', pady=5)
    
    # Чекбокс администратора
    admin_var = ctk.BooleanVar()
    
    def update_admin_checkbox():
        username = username_entry.get()
        if username and (is_user_admin(username) or has_pending_admin_request(username)):
            admin_checkbox.configure(state='disabled')
        else:
            admin_checkbox.configure(state='normal')
    
    username_entry.bind('<KeyRelease>', lambda e: update_admin_checkbox())
    
    admin_checkbox = ctk.CTkCheckBox(
        register_frame,
        text="Просить путь Сёгуна (Администратор)",
        variable=admin_var,
        fg_color=SAMURAI_RED,
        hover_color=SAMURAI_RED_HOVER,
        text_color=SAMURAI_TEXT,
        font=FONT_PRIMARY
    )
    admin_checkbox.pack(pady=10)
    
    def register():
        username = username_entry.get().strip()
        password = password_entry.get().strip()
        confirm = confirm_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        if password != confirm:
            messagebox.showerror("Ошибка", "Свитки не совпадают")
            return
        
        if len(password) < 4:
            messagebox.showerror("Ошибка", "Свиток должен содержать минимум 4 символа")
            return
        
        try:
            Avtorization.get(Avtorization.username == username)
            messagebox.showerror("Ошибка", "Воин с таким именем уже существует")
        except Avtorization.DoesNotExist:
            if is_user_admin(username):
                messagebox.showerror("Ошибка", "Этот воин уже Сёгун")
                return
            
            if has_pending_admin_request(username):
                messagebox.showerror("Ошибка", "У вас уже есть прошение")
                return
            
            # Создаем пользователя
            Avtorization.create(
                username=username,
                password=hash_password(password),
                role='пользователь'
            )
            
            # Заявка на администрирование
            if admin_var.get():
                if is_user_admin(username):
                    messagebox.showerror("Ошибка", "Этот воин уже Сёгун")
                    return
                
                if has_pending_admin_request(username):
                    messagebox.showerror("Ошибка", "У вас уже есть прошение")
                    return
                
                AdminRequests.create(
                    username=username,
                    status='ожидание'
                )
                
                messagebox.showinfo("Успех", 
                                  "Путь открыт! Ваше прошение отправлено Сёгуну.\n\n" +
                                  "После одобрения токен будет сохранен в свиток.")
            else:
                messagebox.showinfo("Успех", "Путь открыт!")
            
            show_auth_window()
    
    create_samurai_button(register_frame, "Создать путь", register).pack(pady=20)
    
    # Ссылка на вход
    def switch_to_login():
        show_auth_window()
    
    login_link = create_samurai_label(register_frame, "Уже есть путь? Войти", 
                                    text_color=SAMURAI_GOLD, font=('Segoe UI', 10, 'underline'))
    login_link.pack(pady=10)
    login_link.bind("<Button-1>", lambda e: switch_to_login())

def create_first_admin():
    try:
        admin_count = Avtorization.select().where(Avtorization.role == 'администратор').count()
        if admin_count == 0:
            first_admin_username = "admin"
            first_admin_password = "admin123"
            
            try:
                Avtorization.get(Avtorization.username == first_admin_username)
            except Avtorization.DoesNotExist:
                Avtorization.create(
                    username=first_admin_username,
                    password=hash_password(first_admin_password),
                    role='администратор',
                    is_main_admin=True
                )
                logger.info(f"Создан первый администратор: {first_admin_username}")
                messagebox.showinfo("Первый Сёгун", 
                                  f"Создан первый Сёгун:\n" +
                                  f"Имя: {first_admin_username}\n" +
                                  f"Свиток: {first_admin_password}\n\n" +
                                  f"Используйте эти знания для входа.")
    except Exception as e:
        logger.error(f"Ошибка создания первого администратора: {e}")

def show_ban_appeal_window(username):
    appeal_win = ctk.CTkToplevel(root)
    appeal_win.title("Суд чести - Апелляция")
    appeal_win.geometry("500x550")
    appeal_win.configure(fg_color=SAMURAI_BG)
    appeal_win.transient(root)
    appeal_win.grab_set()
    
    # Основной контейнер
    main_container = create_samurai_frame(appeal_win, fg_color=SAMURAI_BG)
    main_container.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_container, f"Воин {username} изгнан", 
                        font=FONT_HEADER, text_color=SAMURAI_RED).pack(pady=10)
    
    # Информация о бане
    try:
        ban_info = UserBan.get(UserBan.username == username, UserBan.is_active == True)
        create_samurai_label(main_container, f"Судья: {ban_info.banned_by}", 
                            text_color=SAMURAI_TEXT).pack()
        create_samurai_label(main_container, f"Причина: {ban_info.ban_reason}", 
                            text_color=SAMURAI_TEXT).pack(pady=5)
    except UserBan.DoesNotExist:
        create_samurai_label(main_container, "Записи о бесчестии не найдены", 
                            text_color=SAMURAI_TEXT).pack()
    
    # Выбор администратора
    create_samurai_label(main_container, "Кому направить прошение:", 
                        text_color=SAMURAI_GOLD).pack(pady=(20, 5))
    
    try:
        main_admin = Avtorization.get(Avtorization.is_main_admin == True)
        admin_names = [main_admin.username]
        
        ban_info = UserBan.get(UserBan.username == username, UserBan.is_active == True)
        if ban_info and ban_info.banned_by != main_admin.username:
            admin_names.append(ban_info.banned_by)
    except:
        admin_names = ["admin"]

    admin_combobox = ctk.CTkComboBox(
        main_container, 
        values=admin_names,
        fg_color=SAMURAI_PANEL,
        border_color=SAMURAI_GOLD,
        button_color=SAMURAI_RED,
        dropdown_fg_color=SAMURAI_PANEL,
        dropdown_text_color=SAMURAI_TEXT
    )
    admin_combobox.set(admin_names[0])
    admin_combobox.pack(pady=5)
    
    # Поле для сообщения с скроллбаром
    create_samurai_label(main_container, "Ваше слово:", 
                        text_color=SAMURAI_GOLD).pack(pady=(10, 5))
    
    # Используем скроллируемое текстовое поле
    msg_text = create_scrollable_textbox(main_container, height=150, width=460)
    msg_text.pack(fill='x', pady=5)
    
    def send_appeal():
        msg = msg_text.get("1.0", "end").strip()
        if not msg:
            messagebox.showerror("Ошибка", "Напишите ваше слово")
            return
        
        selected_admin = admin_combobox.get()
        if not selected_admin:
            messagebox.showerror("Ошибка", "Выберите судью")
            return
        
        try:
            BanAppeal.create(
                username=username,
                message=msg,
                admin_recipient=selected_admin
            )
            messagebox.showinfo("Отправлено", f"Ваше прошение отправлено {selected_admin}.")
            appeal_win.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось отправить прошение: {str(e)}")
    
    # Кнопки
    btn_frame = create_samurai_frame(appeal_win, fg_color=SAMURAI_BG)
    btn_frame.pack(side='bottom', pady=20)
    
    create_samurai_button(btn_frame, "Отправить прошение", send_appeal).pack(side='left', padx=10)
    create_samurai_button(btn_frame, "Отмена", appeal_win.destroy, 
                         color=SAMURAI_PANEL, hover_color="#333").pack(side='left', padx=10)

def complete_admin_registration_window(username):
    complete_win = ctk.CTkToplevel(root)
    complete_win.title("Посвящение в Сёгуны")
    complete_win.geometry("500x350")
    complete_win.configure(fg_color=SAMURAI_BG)
    complete_win.transient(root)
    complete_win.grab_set()
    
    main_frame = create_samurai_frame(complete_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, "Посвящение в Сёгуны", 
                        font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=10)
    
    create_samurai_label(main_frame, f"Для воина: {username}", 
                        text_color=SAMURAI_TEXT).pack(pady=5)
    
    create_samurai_label(main_frame, "Введите токен посвящения из свитка:", 
                        text_color=SAMURAI_TEXT, font=('Segoe UI', 10)).pack(pady=10)
    
    token_entry = create_samurai_entry(main_frame, "Токен посвящения")
    token_entry.pack(pady=10)
    
    def complete_registration():
        token = token_entry.get()
        
        if not token:
            messagebox.showerror("Ошибка", "Введите токен")
            return
        
        try:
            request = AdminRequests.get(
                (AdminRequests.username == username) & 
                (AdminRequests.status == 'одобрено') &
                (AdminRequests.admin_token == token)
            )
            
            user = Avtorization.get(Avtorization.username == username)
            user.role = 'администратор'
            user.save()
            
            messagebox.showinfo("Успех", "Посвящение завершено! Теперь вы Сёгун.")
            complete_win.destroy()
            show_auth_window()
            
        except AdminRequests.DoesNotExist:
            messagebox.showerror("Ошибка", "Неверный токен или прошение не принято")
        except Avtorization.DoesNotExist:
            messagebox.showerror("Ошибка", "Воин не найден")
    
    create_samurai_button(main_frame, "Завершить посвящение", complete_registration).pack(pady=20)
    
    # Информация о файле с токеном
    info_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    info_frame.pack(pady=10)
    
    create_samurai_label(info_frame, "Токен находится в свитке:", 
                        text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 10, 'bold')).pack()
    
    token_filename = f"tokens/{username}_token.txt"
    create_samurai_label(info_frame, token_filename, 
                        text_color=SAMURAI_GOLD, font=('Segoe UI', 10)).pack()
    
    create_samurai_label(main_frame, "Если свиток утерян, обратитесь к главному Сёгуну", 
                        text_color=SAMURAI_RED, font=('Segoe UI', 9)).pack(pady=10)

# ========== ГЛАВНОЕ ОКНО ==========

def home_window():
    if not check_auth():
        return
        
    for widget in root.winfo_children():
        widget.destroy()
    
    # --- ВЕРХНЯЯ ПАНЕЛЬ ---
    nav_frame = create_samurai_frame(root, fg_color="black")
    nav_frame.pack(fill='x', side='top')
    
    # Логотип
    logo_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    logo_frame.pack(side='left', padx=20, pady=10)
    
    try:
        icon_image = Image.open("content/icon.png")
        icon_ctk_image = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(40, 40))
        icon_label = ctk.CTkLabel(logo_frame, image=icon_ctk_image, text="")
        icon_label.pack(side='left', padx=5)
    except Exception:
        pass
    
    create_samurai_label(logo_frame, "BUSHIDO", font=("Impact", 24), text_color=SAMURAI_RED).pack(side='left', padx=5)
    
    # Навигация
    nav_buttons_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    nav_buttons_frame.pack(side='left', padx=50, pady=10)
    
    def create_nav_button(text, command, is_active=False):
        color = SAMURAI_RED if is_active else "transparent"
        btn = create_samurai_button(nav_buttons_frame, text, command, color=color, 
                                   hover_color=SAMURAI_RED_HOVER, width=120)
        
        def on_enter(event):
            if not is_active:
                btn.configure(fg_color=SAMURAI_RED_HOVER)
                
        def on_leave(event):
            if not is_active:
                btn.configure(fg_color=color)
                
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    create_nav_button("Главная", lambda: show_loading_screen(home_window), True).pack(side='left', padx=5)
    create_nav_button("Мотивация", lambda: show_loading_screen(motivation_window)).pack(side='left', padx=5)
    create_nav_button("Аффирмации", lambda: show_loading_screen(affirmation_window)).pack(side='left', padx=5)
    create_nav_button("Юмор", lambda: show_loading_screen(funny_quotes_window)).pack(side='left', padx=5)
    
    # Пользователь
    user_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    user_frame.pack(side='right', padx=20, pady=10)
    
    create_samurai_label(user_frame, current_user['username'], 
                        font=FONT_BOLD, text_color=SAMURAI_GOLD).pack(side='left', padx=10)
    
    create_samurai_button(user_frame, "Выйти", logout, width=80).pack(side='left', padx=5)
    
    if current_user['role'] == 'администратор':
        create_samurai_button(user_frame, "Сёгун", developer_window, 
                             color=SAMURAI_RED, width=80).pack(side='left', padx=5)
    
    separator = ctk.CTkFrame(root, height=2, fg_color=SAMURAI_GOLD, corner_radius=0)
    separator.pack(fill='x', side='top')
    
    # --- ОБНОВЛЕННЫЙ СКРОЛЛИНГ (Без следов) ---

    # Создаем ScrollableFrame вместо Canvas + Scrollbar
    # Это нативный виджет, который убирает "гостинг" (следы) при прокрутке
    main_scroll_frame = ctk.CTkScrollableFrame(
        root,
        fg_color=SAMURAI_BG,             # Цвет фона контента
        scrollbar_button_color=SAMURAI_RED,      # Цвет ползунка (как в теме)
        scrollbar_button_hover_color=SAMURAI_RED_HOVER, # Цвет при наведении
        scrollbar_fg_color=SAMURAI_PANEL,        # Цвет фона полосы скроллбара
        corner_radius=0,
        label_fg_color=SAMURAI_BG                # Цвет фона области скроллбара
    )
    main_scroll_frame.pack(fill='both', expand=True, padx=0, pady=0)
    
    # --- СОДЕРЖИМОЕ ГЛАВНОЙ СТРАНИЦЫ ---

    # Важно: все элементы теперь добавляются в main_scroll_frame

    center_container = create_samurai_frame(main_scroll_frame, fg_color=SAMURAI_BG)
    center_container.pack(expand=True, fill='both', padx=30, pady=20)
    
    # --- ЖИВЫЕ ЧАСЫ ---
    time_frame = create_samurai_frame(center_container, fg_color=SAMURAI_BG)
    time_frame.pack(pady=(10, 5))
    
    time_label = create_samurai_label(time_frame, text="", font=("Segoe UI", 36, "bold"), text_color=SAMURAI_TEXT)
    time_label.pack()
    
    date_label = create_samurai_label(time_frame, text="", font=("Segoe UI", 14), text_color=SAMURAI_GOLD)
    date_label.pack()

    def update_clock():
        if time_label.winfo_exists():
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            current_date = now.strftime("%d %B %Y")
            
            time_label.configure(text=current_time)
            date_label.configure(text=current_date)
            time_label.after(1000, update_clock)
            
    update_clock()
    
    # --- ИЗОБРАЖЕНИЕ ---
    try:
        main_img = Image.open("content/1.png")
        
        original_width, original_height = main_img.size
        target_width = 700 
        target_height = int((target_width * original_height) / original_width)
        
        main_img = main_img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        main_ctk_image = ctk.CTkImage(light_image=main_img, dark_image=main_img, size=(target_width, target_height))
        
        img_label = ctk.CTkLabel(center_container, image=main_ctk_image, text="", fg_color=SAMURAI_BG)
        img_label.image = main_ctk_image
        img_label.pack(pady=(10, 20))
        
    except Exception:
        create_samurai_label(center_container, "[Изображение самурая]", 
                           text_color=SAMURAI_TEXT_SECONDARY).pack(pady=50)
    
    # Инфо-карточка
    info_card_container = create_samurai_frame(center_container, fg_color=SAMURAI_BG)
    info_card_container.pack(fill='x', pady=(0, 20))
    
    info_card = create_samurai_frame(info_card_container, border_color=SAMURAI_GOLD)
    info_card.pack(fill='x', padx=20)
    
    create_samurai_label(info_card, "Добро пожаловать, Воин", 
                        font=FONT_TITLE, text_color="white").pack(pady=20)
    
    developer_info = create_samurai_label(
        info_card,
        text='Разработчик: Оноприенко Р. А. \n\n' +
             'Телефон: +79632181240\n' +
             'Email: raleksandrovic619@gmail.com',
        text_color=SAMURAI_TEXT_SECONDARY,
        font=FONT_PRIMARY,
        justify='center'
    )
    developer_info.pack(pady=(0, 20))
    
    # --- СОЦСЕТИ ---
    social_frame = create_samurai_frame(center_container, fg_color=SAMURAI_BG)
    social_frame.pack(pady=20)

    def open_link(url):
        webbrowser.open_new(url)

    def create_social_button(image_path, url, size=50):
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
                
                # Используем SAMURAI_BG или transparent
                btn = ctk.CTkButton(
                    social_frame, 
                    image=ctk_image, 
                    text="", 
                    width=size+10, 
                    height=size+10,
                    fg_color="transparent", 
                    hover_color=SAMURAI_PANEL,
                    command=lambda: open_link(url)
                )
                
                def on_enter(event):
                    btn.configure(width=size+15, height=size+15)
                    
                def on_leave(event):
                    btn.configure(width=size+10, height=size+10)
                    
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
                
                return btn
            return None
        except Exception:
            return None

    tg_btn = create_social_button("content/tg.png", "https://t.me/GoodFleck")
    if tg_btn: tg_btn.pack(side='left', padx=20)

    x_btn = create_social_button("content/x.png", "https://x.com/Wolv_18")
    if x_btn: x_btn.pack(side='left', padx=20)

    vk_btn = create_social_button("content/vk.png", "https://vk.com/huwzan")
    if vk_btn: vk_btn.pack(side='left', padx=20)

    # Пустой блок для отступа снизу и обеспечения минимальной высоты для скроллбара
    ctk.CTkLabel(center_container, text="", height=100, fg_color=SAMURAI_BG).pack()

# ========== ОКНА С ЦИТАТАМИ ==========

def motivation_window():
    show_quote_window('motivation', 'Мотивационные цитаты', Motivation)

def affirmation_window():
    show_quote_window('affirmation', 'Аффирмации', Affirmation)

def funny_quotes_window():
    show_quote_window('funny', 'Смешные цитаты', FunnyQuote)

def show_quote_window(quote_type, title, ModelClass):
    if not check_auth():
        return
        
    for widget in root.winfo_children():
        widget.destroy()
    
    # --- ВЕРХНЯЯ ПАНЕЛЬ (NAV BAR) ---
    nav_frame = create_samurai_frame(root, fg_color="black")
    nav_frame.pack(fill='x', side='top')
    
    logo_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    logo_frame.pack(side='left', padx=20, pady=10)
    
    try:
        icon_image = Image.open("content/icon.png")
        icon_ctk_image = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(40, 40))
        icon_label = ctk.CTkLabel(logo_frame, image=icon_ctk_image, text="")
        icon_label.pack(side='left', padx=5)
    except:
        pass
    
    create_samurai_label(logo_frame, "BUSHIDO", font=("Impact", 24), text_color=SAMURAI_RED).pack(side='left', padx=5)
    
    nav_buttons_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    nav_buttons_frame.pack(side='left', padx=50, pady=10)
    
    def create_nav_button(text, command, is_active=False):
        color = SAMURAI_RED if is_active else "transparent"
        btn = create_samurai_button(nav_buttons_frame, text, command, color=color, 
                                   hover_color=SAMURAI_RED_HOVER, width=120)
        
        # Анимация для кнопок навигации
        def on_enter(event):
            if not is_active:
                btn.configure(fg_color=SAMURAI_RED_HOVER)
                
        def on_leave(event):
            if not is_active:
                btn.configure(fg_color=color)
                
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    create_nav_button("Главная", lambda: show_loading_screen(home_window)).pack(side='left', padx=5)
    
    is_motivation = quote_type == 'motivation'
    is_affirmation = quote_type == 'affirmation'
    is_funny = quote_type == 'funny'
    
    create_nav_button("Мотивация", lambda: show_loading_screen(motivation_window), is_motivation).pack(side='left', padx=5)
    create_nav_button("Аффирмации", lambda: show_loading_screen(affirmation_window), is_affirmation).pack(side='left', padx=5)
    create_nav_button("Юмор", lambda: show_loading_screen(funny_quotes_window), is_funny).pack(side='left', padx=5)
    
    user_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    user_frame.pack(side='right', padx=20, pady=10)
    
    create_samurai_label(user_frame, current_user['username'], 
                        font=FONT_BOLD, text_color=SAMURAI_GOLD).pack(side='left', padx=10)
    
    create_samurai_button(user_frame, "Выйти", logout, width=80).pack(side='left', padx=5)
    
    if current_user['role'] == 'администратор':
        create_samurai_button(user_frame, "Сёгун", developer_window, 
                             color=SAMURAI_RED, width=80).pack(side='left', padx=5)
    
    # Тонкая желтая линия
    separator = ctk.CTkFrame(root, height=2, fg_color=SAMURAI_GOLD, corner_radius=0)
    separator.pack(fill='x', side='top', pady=(0, 10))
    
    # --- ОСНОВНОЙ КОНТЕНТ ---
    content_frame = ctk.CTkFrame(root, fg_color=SAMURAI_BG)
    content_frame.pack(fill='both', expand=True)
    
    create_samurai_label(content_frame, title, font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=20)
    
    # Получаем disliked цитаты (чтобы не показывать их)
    disliked_ids = [
        r.quote_id for r in UserReaction.select().where(
            (UserReaction.username == current_user['username']) &
            (UserReaction.quote_type == quote_type) &
            (UserReaction.reaction == 'dislike')
        )
    ]
    
    # Загружаем цитаты
    try:
        all_quotes = ModelClass.select().where(ModelClass.is_deleted == False)
        quotes = [q for q in all_quotes if q.id not in disliked_ids]
        
        if not quotes:
            create_samurai_label(content_frame, "Нет цитат в базе данных", 
                               text_color=SAMURAI_TEXT_SECONDARY).pack(pady=50)
            return
            
        current_quote_index = 0
        
        # Основной контейнер слайдера
        slider_frame = create_samurai_frame(content_frame, fg_color=SAMURAI_BG)
        slider_frame.pack(pady=10, padx=50, fill='both', expand=True)
        
        # Карточка цитаты
        quote_card = create_samurai_frame(slider_frame, border_color=SAMURAI_GOLD, height=300)
        quote_card.pack(pady=10, fill='x')
        quote_card.pack_propagate(False) # Фиксируем размер карточки
        
        # Текст цитаты
        quote_text_frame = create_samurai_frame(quote_card, fg_color=SAMURAI_CARD)
        quote_text_frame.pack(expand=True, fill='both', padx=30, pady=30)
        
        quote_label = create_samurai_label(
            quote_text_frame, 
            text="", 
            font=("Georgia", 18, "italic"),
            text_color="white",
            wraplength=800,
            justify='center'
        )
        quote_label.pack(expand=True)
        
        author_label = create_samurai_label(
            quote_text_frame,
            text="",
            font=FONT_PRIMARY,
            text_color=SAMURAI_GOLD
        )
        author_label.pack(pady=(20, 0))
        
        # --- БЛОК РЕАКЦИЙ (ЛАЙКИ) ---
        reaction_frame = create_samurai_frame(slider_frame, fg_color=SAMURAI_BG)
        reaction_frame.pack(pady=10)
        
        # Счетчик лайков
        likes_count_label = create_samurai_label(
            reaction_frame,
            text="Честь: 0",
            font=FONT_BOLD,
            text_color=SAMURAI_GREEN
        )
        likes_count_label.pack(side='left', padx=20)
        
        # Функции логики
        def update_likes_count():
            if not quotes: return
            current_q = quotes[current_quote_index]
            try:
                likes_count = UserReaction.select().where(
                    (UserReaction.quote_id == current_q.id) &
                    (UserReaction.quote_type == quote_type) &
                    (UserReaction.reaction == 'like')
                ).count()
                likes_count_label.configure(text=f"Честь: {likes_count}")
            except: pass

        def update_quote_display():
            if quotes and quote_label.winfo_exists():
                quote = quotes[current_quote_index]
                quote_label.configure(text=f"\"{quote.text}\"")
                author_label.configure(text=f"— {quote.author}")
                counter_label.configure(text=f"{current_quote_index + 1} из {len(quotes)}")
                update_likes_count()
        
        def set_reaction(reaction_type):
            nonlocal current_quote_index
            if not quotes: return
            current_q = quotes[current_quote_index]
            try:
                UserReaction.delete().where(
                    (UserReaction.username == current_user['username']) &
                    (UserReaction.quote_id == current_q.id) &
                    (UserReaction.quote_type == quote_type)
                ).execute()
                
                UserReaction.create(
                    username=current_user['username'],
                    quote_id=current_q.id,
                    quote_type=quote_type,
                    reaction=reaction_type
                )
                
                if reaction_type == 'dislike':
                    quotes.pop(current_quote_index)
                    if not quotes:
                        quote_label.configure(text="Пусто")
                        return
                    if current_quote_index >= len(quotes):
                        current_quote_index = 0
                    update_quote_display()
                else:
                    update_likes_count()
            except: pass

        # Кнопки реакций
        reaction_buttons_frame = create_samurai_frame(reaction_frame, fg_color=SAMURAI_BG)
        reaction_buttons_frame.pack(side='right')
        
        create_samurai_button(reaction_buttons_frame, "👍 Честь", lambda: set_reaction('like'),
                            color=SAMURAI_GREEN, hover_color=SAMURAI_GREEN_HOVER, width=100).pack(side='left', padx=5)
        
        create_samurai_button(reaction_buttons_frame, "👎 Бесчестие", lambda: set_reaction('dislike'),
                            color=SAMURAI_RED, hover_color=SAMURAI_RED_HOVER, width=100).pack(side='left', padx=5)
        
        # Навигация стрелками
        nav_controls_frame = create_samurai_frame(slider_frame, fg_color=SAMURAI_BG)
        nav_controls_frame.pack(pady=20)
        
        def next_quote():
            nonlocal current_quote_index
            current_quote_index = (current_quote_index + 1) % len(quotes)
            update_quote_display()
        
        def prev_quote():
            nonlocal current_quote_index
            current_quote_index = (current_quote_index - 1) % len(quotes)
            update_quote_display()
            
        def show_random_quote():
            nonlocal current_quote_index
            current_quote_index = random.randint(0, len(quotes) - 1)
            update_quote_display()

        # Кнопка НАЗАД (<)
        create_samurai_button(
            nav_controls_frame, 
            "<", 
            prev_quote,
            width=50, 
            height=40,
            font=("Arial", 16, "bold")
        ).pack(side='left', padx=20)
        
        # СЧЕТЧИК (По центру между стрелками)
        counter_label = create_samurai_label(
            nav_controls_frame,
            text="0 / 0",
            font=("Segoe UI", 16, "bold"),
            text_color=SAMURAI_GOLD
        )
        counter_label.pack(side='left', padx=20)
        
        # Кнопка ВПЕРЕД (>) 
        create_samurai_button(
            nav_controls_frame, 
            ">", 
            next_quote,
            width=50, 
            height=40,
            font=("Arial", 16, "bold")
        ).pack(side='left', padx=20)
        
        # Кнопка СЛУЧАЙНАЯ (снизу)
        create_samurai_button(
            slider_frame,
            "🎲 Случайная мудрость",
            show_random_quote,
            color=SAMURAI_PANEL,
            hover_color="#333",
            width=200
        ).pack(pady=(0, 20))
        
        # Бинды клавиш
        def on_key_press(event):
            try:
                if event.keysym == 'Left': prev_quote()
                elif event.keysym == 'Right': next_quote()
                elif event.keysym == 'space': show_random_quote()
            except: pass
        
        key_bindings = [
            root.bind('<Left>', on_key_press),
            root.bind('<Right>', on_key_press),
            root.bind('<space>', on_key_press)
        ]
        
        def cleanup():
            for b in key_bindings:
                try: 
                    root.unbind('<Left>', b)
                    root.unbind('<Right>', b)
                    root.unbind('<space>', b)
                except: pass
        
        content_frame.bind('<Destroy>', lambda e: cleanup())
        
        # Запуск отображения
        update_quote_display()
        
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        create_samurai_label(content_frame, "Ошибка загрузки свитков", text_color=SAMURAI_RED).pack()

# ========== ОКНО РАЗРАБОТЧИКА ==========

def developer_window():
    if not check_auth():
        return
    
    dev_win = ctk.CTkToplevel(root)
    dev_win.title("Сёгун - Панель управления")
    dev_win.geometry("1100x750")
    dev_win.configure(fg_color=SAMURAI_BG)
    dev_win.transient(root)
    dev_win.grab_set()
    
    main_frame = create_samurai_frame(dev_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, "Панель Сёгуна", font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=10)
    
    # Кнопка управления контентом для главного администратора
    if is_main_admin():
        content_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_PANEL)
        content_frame.pack(fill='x', padx=20, pady=10)
        
        create_samurai_button(
            content_frame, 
            "📜 Управление свитками (БД)", 
            manage_quotes_window,
            width=400
        ).pack(pady=10)
    
    # Вкладки
    tabview = ctk.CTkTabview(
        main_frame,
        fg_color=SAMURAI_PANEL,
        segmented_button_fg_color=SAMURAI_BG,
        segmented_button_selected_color=SAMURAI_RED,
        segmented_button_selected_hover_color=SAMURAI_RED_HOVER,
        text_color=SAMURAI_TEXT
    )
    tabview.pack(fill='both', expand=True, padx=20, pady=10)
    
    # Добавляем вкладки
    if is_main_admin():
        tabview.add("Заявки")
        tabview.add("Летопись") # Новая вкладка для логов
        
    tabview.add("Баны")
    tabview.add("Апелляции")
    
    # Загружаем содержимое вкладок
    if is_main_admin():
        load_requests_tab(tabview.tab("Заявки"))
        load_logs_tab(tabview.tab("Летопись")) # Загрузка логов
        
    load_bans_tab(tabview.tab("Баны"))
    load_appeals_tab(tabview.tab("Апелляции"))
    
    create_samurai_button(main_frame, "Закрыть", dev_win.destroy).pack(pady=10)

def load_logs_tab(parent):
    """Загрузка логов действий администраторов"""
    create_samurai_label(parent, "Действия Сёгунов:", 
                       font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(anchor='w', pady=(0, 10))
    
    # Контейнер для таблицы
    table_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    table_frame.pack(fill='both', expand=True)
    
    # Настройка колонок
    columns = ("date", "admin", "action", "target", "details")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    tree.heading("date", text="Дата")
    tree.heading("admin", text="Сёгун")
    tree.heading("action", text="Действие")
    tree.heading("target", text="Цель")
    tree.heading("details", text="Детали")
    
    tree.column("date", width=150)
    tree.column("admin", width=100)
    tree.column("action", width=100)
    tree.column("target", width=100)
    tree.column("details", width=300)
    
    # Скроллбар
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # === ИСПРАВЛЕНИЕ СКРОЛЛИНГА ===
    setup_touchpad_scrolling(tree)
    # ==============================

    def refresh_logs():
        for item in tree.get_children():
            tree.delete(item)
            
        try:
            # Получаем последние 100 действий
            logs = AdminActionLog.select().order_by(AdminActionLog.action_date.desc()).limit(100)
            
            for log in logs:
                date_str = log.action_date.strftime("%d.%m.%Y %H:%M")
                
                # Раскраска действий (опционально через теги, но пока просто текст)
                tree.insert("", "end", values=(
                    date_str,
                    log.admin_username,
                    log.action_type,
                    log.target_username,
                    log.details
                ))
        except Exception as e:
            logger.error(f"Ошибка загрузки логов: {e}")
            
    # Кнопка обновления
    btn_frame = create_samurai_frame(parent, fg_color="transparent")
    btn_frame.pack(fill='x', pady=5)
    create_samurai_button(btn_frame, "Обновить летопись", refresh_logs, width=200).pack(side='right')
    
    refresh_logs()

def load_requests_tab(parent):
    """Загрузка вкладки управления заявками"""
    # Информация о текущем пользователе
    status_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    status_frame.pack(fill='x', pady=5)
    
    if is_main_admin():
        create_samurai_label(status_frame, "Статус: Главный Сёгун", 
                           text_color=SAMURAI_GREEN, font=FONT_BOLD).pack(side='left')
    else:
        create_samurai_label(status_frame, "Статус: Сёгун", 
                           text_color=SAMURAI_GOLD, font=FONT_BOLD).pack(side='left')
    
    # Токен пользователя
    user_token = get_current_user_token()
    if user_token:
        token_frame = create_samurai_frame(parent, fg_color=SAMURAI_PANEL)
        token_frame.pack(fill='x', pady=10)
        
        create_samurai_label(token_frame, "Ваш токен посвящения:", 
                           font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w', padx=10, pady=5)
        
        token_display = create_samurai_label(
            token_frame, 
            user_token,
            font=('Consolas', 10),
            text_color=SAMURAI_GOLD
        )
        token_display.pack(fill='x', padx=10, pady=5)
        
        token_filename = f"tokens/{current_user['username']}_token.txt"
        create_samurai_label(token_frame, f"Свиток: {token_filename}", 
                           font=('Segoe UI', 9), text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w', padx=10, pady=(0, 5))
    
    # Список заявок
    create_samurai_label(parent, "Прошения о посвящении:", 
                       font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(anchor='w', pady=(20, 10))
    
    requests_container = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    requests_container.pack(fill='both', expand=True)
    
    def load_requests():
        for widget in requests_container.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
        
        try:
            pending_requests = AdminRequests.select().where(AdminRequests.status == 'ожидание')

            if not pending_requests:
                create_samurai_label(requests_container, "Нет ожидающих прошений", 
                                   text_color=SAMURAI_TEXT_SECONDARY).pack(pady=20)
                return
            
            for request in pending_requests:
                request_frame = create_samurai_frame(requests_container, border_color=SAMURAI_GOLD)
                request_frame.pack(fill='x', pady=5, padx=5)
                
                info_frame = create_samurai_frame(request_frame, fg_color=SAMURAI_PANEL)
                info_frame.pack(fill='x', padx=10, pady=5)
                
                create_samurai_label(info_frame, f"Воин: {request.username}", 
                                   font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w')
                create_samurai_label(info_frame, f"Дата прошения: {request.request_date}", 
                                   font=('Segoe UI', 10), text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w')
                
                btn_frame = create_samurai_frame(request_frame, fg_color=SAMURAI_PANEL)
                btn_frame.pack(fill='x', padx=10, pady=5)
                
                def approve_request(req=request):
                    try:
                        admin_token = generate_admin_token()
                        token_file = save_token_to_file(req.username, admin_token)
                        
                        req.status = 'одобрено'
                        req.reviewed_by = current_user['username']
                        req.admin_token = admin_token
                        req.save()
                        
                        messagebox.showinfo("Успех", 
                                          f"Прошение воина {req.username} принято!\n\n" +
                                          f"Токен сохранен в свиток: {token_file}")
                        load_requests()
                    except Exception as e:
                        logger.error(f"Ошибка принятия прошения: {str(e)}")
                        messagebox.showerror("Ошибка", f"Ошибка при принятии прошения: {str(e)}")
                
                def reject_request(req=request):
                    req.status = 'отклонено'
                    req.reviewed_by = current_user['username']
                    req.save()
                    messagebox.showinfo("Отклонено", f"Прошение воина {req.username} отклонено!")
                    load_requests()
                
                create_samurai_button(
                    btn_frame, 
                    "Принять", 
                    approve_request,
                    color=SAMURAI_GREEN,
                    hover_color=SAMURAI_GREEN_HOVER,
                    width=100
                ).pack(side='left', padx=5)
                
                create_samurai_button(
                    btn_frame, 
                    "Отклонить", 
                    reject_request,
                    color=SAMURAI_RED,
                    hover_color=SAMURAI_RED_HOVER,
                    width=100
                ).pack(side='left', padx=5)
        
        except Exception as e:
            logger.error(f"Ошибка загрузки прошений: {str(e)}")
            create_samurai_label(
                requests_container, 
                f"Ошибка загрузки прошений: {str(e)}", 
                text_color=SAMURAI_RED
            ).pack(pady=20)
    
    create_samurai_button(parent, "Обновить прошения", load_requests).pack(pady=10)
    load_requests()

def load_bans_tab(parent):
    """Загрузка вкладки управления банами"""
    create_samurai_label(parent, "Управление изгнаниями", 
                       font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(anchor='w', pady=(0, 10))
    
    # Форма бана
    ban_form_frame = create_samurai_frame(parent, fg_color=SAMURAI_PANEL)
    ban_form_frame.pack(fill='x', pady=10)
    
    create_samurai_label(ban_form_frame, "Изгнать воина:", 
                       font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w', padx=10, pady=5)
    
    ban_input_frame = create_samurai_frame(ban_form_frame, fg_color=SAMURAI_PANEL)
    ban_input_frame.pack(fill='x', padx=10, pady=5)
    
    create_samurai_label(ban_input_frame, "Имя воина:", 
                       text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    # Получаем список пользователей для бана
    def get_users_for_ban():
        try:
            users = Avtorization.select().where(
                (Avtorization.username != current_user['username'])  # Исключаем себя
            )
            
            # Фильтруем по правам
            available_users = []
            for user in users:
                if can_ban_user(user.username):
                    available_users.append(user.username)
                    
            return available_users
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []
    
    ban_user_combobox = ctk.CTkComboBox(
        ban_input_frame,
        values=get_users_for_ban(),
        fg_color=SAMURAI_PANEL,
        border_color=SAMURAI_GOLD,
        button_color=SAMURAI_RED,
        dropdown_fg_color=SAMURAI_PANEL,
        dropdown_text_color=SAMURAI_TEXT,
        width=200
    )
    if get_users_for_ban():
        ban_user_combobox.set(get_users_for_ban()[0])
    ban_user_combobox.pack(side='left', padx=5)
    
    create_samurai_label(ban_input_frame, "Причина:", 
                       text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    ban_reason_entry = create_samurai_entry(ban_input_frame, width=200)
    ban_reason_entry.pack(side='left', padx=5)
    ban_reason_entry.insert(0, "Нарушение кодекса")
    
    def refresh_ban_users():
        """Обновить список пользователей для бана"""
        ban_user_combobox.configure(values=get_users_for_ban())
        if get_users_for_ban():
            ban_user_combobox.set(get_users_for_ban()[0])
    
    def perform_ban():
        username = ban_user_combobox.get().strip()
        reason = ban_reason_entry.get().strip()
        
        if not username:
            messagebox.showerror("Ошибка", "Выберите воина для изгнания")
            return
        
        result = ban_user(username, reason)
        if result["status"] == "success":
            messagebox.showinfo("Успех", f"Воин {username} изгнан\nПричина: {reason}")
            refresh_ban_users()  # Обновляем список после бана
            update_banned_list()
        else:
            messagebox.showerror("Ошибка", result["message"])
    
    create_samurai_button(ban_input_frame, "Изгнать", perform_ban).pack(side='left', padx=10)
    create_samurai_button(ban_input_frame, "Обновить список", refresh_ban_users, 
                         color=SAMURAI_PANEL, hover_color="#333").pack(side='left', padx=5)
    
    # Список изгнанных
    create_samurai_label(parent, "Изгнанные воины:", 
                       font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w', pady=(20, 10))
    
    banned_container = ctk.CTkScrollableFrame(parent, fg_color=SAMURAI_BG)
    banned_container.pack(fill='both', expand=True)
    
    def update_banned_list():
        for widget in banned_container.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
        
        try:
            active_bans = UserBan.select().where(UserBan.is_active == True)
            
            if not active_bans:
                create_samurai_label(banned_container, "Нет изгнанных воинов", 
                                   text_color=SAMURAI_TEXT_SECONDARY).pack(pady=20)
                return
            
            for ban in active_bans:
                ban_frame = create_samurai_frame(banned_container, border_color=SAMURAI_RED)
                ban_frame.pack(fill='x', pady=2, padx=5)
                
                info_frame = create_samurai_frame(ban_frame, fg_color=SAMURAI_PANEL)
                info_frame.pack(fill='x', padx=10, pady=5)
                
                create_samurai_label(info_frame, f"Воин: {ban.username}", 
                                   font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w')
                create_samurai_label(info_frame, f"Изгнан Сёгуном: {ban.banned_by}", 
                                   text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w')
                create_samurai_label(info_frame, f"Причина: {ban.ban_reason}", 
                                   text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w')
                
                ban_date = ban.ban_date.strftime("%d.%m.%Y %H:%M") if ban.ban_date else "Неизвестно"
                create_samurai_label(info_frame, f"Дата изгнания: {ban_date}", 
                                   text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w')
                
                btn_frame = create_samurai_frame(ban_frame, fg_color=SAMURAI_PANEL)
                btn_frame.pack(fill='x', padx=10, pady=5)
                
                def perform_unban(unban_username=ban.username):
                    result = unban_user(unban_username)
                    if result["status"] == "success":
                        messagebox.showinfo("Успех", result["message"])
                        update_banned_list()
                    else:
                        messagebox.showerror("Ошибка", result["message"])
                
                # Показываем кнопку разбана только если есть права
                if can_unban_user(ban.username):
                    create_samurai_button(
                        btn_frame, 
                        "Вернуть путь", 
                        perform_unban,
                        color=SAMURAI_GREEN,
                        hover_color=SAMURAI_GREEN_HOVER,
                        width=120
                    ).pack(side='right', padx=5)
                else:
                    # Показываем серую неактивную кнопку
                    create_samurai_button(
                        btn_frame, 
                        "Нет прав для возврата", 
                        None,
                        color=SAMURAI_PANEL,
                        hover_color=SAMURAI_PANEL,
                        text_color=SAMURAI_TEXT_SECONDARY,
                        width=120
                    ).pack(side='right', padx=5)
        
        except Exception as e:
            logger.error(f"Ошибка загрузки изгнанных: {e}")
            create_samurai_label(
                banned_container, 
                f"Ошибка загрузки: {str(e)}", 
                text_color=SAMURAI_RED
            ).pack(pady=20)
    
    create_samurai_button(parent, "Обновить список", update_banned_list).pack(pady=10)
    update_banned_list()

def load_appeals_tab(parent):
    """Загрузка вкладки апелляций"""
    create_samurai_label(parent, "Прошения изгнанных:", 
                       font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(anchor='w', pady=(0, 10))
    
    appeals_container = ctk.CTkScrollableFrame(parent, fg_color=SAMURAI_BG)
    appeals_container.pack(fill='both', expand=True)
    
    def refresh_appeals():
        # Проверяем существование контейнера
        if not appeals_container or not appeals_container.winfo_exists():
            return
            
        for widget in appeals_container.winfo_children():
            if widget.winfo_exists():
                widget.destroy()
            
        try:
            # Главный сёгун видит все апелляции
            if is_main_admin():
                appeals = BanAppeal.select().where(BanAppeal.status == 'ожидание')
            else:
                # Обычные сёгуны видят апелляции, адресованные им
                appeals = BanAppeal.select().where(
                    (BanAppeal.status == 'ожидание') & 
                    (BanAppeal.admin_recipient == current_user['username'])
                )
            
            if not appeals:
                if appeals_container.winfo_exists():
                    create_samurai_label(appeals_container, "Нет ожидающих прошений", 
                                       text_color=SAMURAI_TEXT_SECONDARY).pack(pady=20)
                return
            
            for appeal in appeals:
                if not appeals_container.winfo_exists():
                    break
                    
                appeal_frame = create_samurai_frame(appeals_container, border_color=SAMURAI_GOLD)
                appeal_frame.pack(fill='x', pady=5)
                
                create_samurai_label(appeal_frame, f"От: {appeal.username} ({appeal.created_at})", 
                                   font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w', padx=10, pady=5)
                
                admin_recipient = getattr(appeal, 'admin_recipient', 'Не указан')
                create_samurai_label(appeal_frame, f"Сёгуну: {admin_recipient}", 
                                   text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w', padx=10)
                
                create_samurai_label(appeal_frame, f"Слово: {appeal.message}", 
                                   text_color=SAMURAI_TEXT).pack(anchor='w', padx=10, pady=2)
                
                btn_frame = create_samurai_frame(appeal_frame, fg_color=SAMURAI_PANEL)
                btn_frame.pack(fill='x', padx=10, pady=5)
                
                def mark_read(a=appeal):
                    a.status = 'рассмотрено'
                    a.save()
                    refresh_appeals()
                
                def unban_from_appeal(u=appeal.username, a=appeal):
                    result = unban_user(u)
                    if result["status"] == "success":
                        a.status = 'одобрено'
                        a.save()
                        messagebox.showinfo("Успех", f"{u} возвращен на путь")
                        refresh_appeals()
                    else:
                        messagebox.showerror("Ошибка", result["message"])

                create_samurai_button(
                    btn_frame, 
                    "Вернуть путь", 
                    unban_from_appeal,
                    color=SAMURAI_GREEN,
                    hover_color=SAMURAI_GREEN_HOVER,
                    width=120
                ).pack(side='left', padx=5)
                
                create_samurai_button(
                    btn_frame, 
                    "Прочитано", 
                    mark_read,
                    color=SAMURAI_PANEL,
                    hover_color="#333",
                    width=120
                ).pack(side='left', padx=5)
                
        except Exception as e:
            logger.error(f"Ошибка загрузки прошений: {e}")
            if appeals_container.winfo_exists():
                create_samurai_label(
                    appeals_container, 
                    f"Ошибка загрузки: {str(e)}", 
                    text_color=SAMURAI_RED
                ).pack(pady=20)

    create_samurai_button(parent, "Обновить прошения", refresh_appeals).pack(pady=10)
    refresh_appeals()

# ========== ФУНКЦИИ УПРАВЛЕНИЯ КОНТЕНТОМ ==========

def manage_quotes_window():
    if not is_main_admin():
        messagebox.showerror("Ошибка", "Только главный Сёгун может управлять свитками")
        return
        
    manage_win = ctk.CTkToplevel(root)
    manage_win.title("Свитки мудрости - Управление")
    manage_win.geometry("1200x800")
    manage_win.configure(fg_color=SAMURAI_BG)
    manage_win.transient(root)
    manage_win.grab_set()
    
    main_frame = create_samurai_frame(manage_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, "Управление свитками мудрости", 
                       font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=10)
    
    # Вкладки
    tabview = ctk.CTkTabview(
        main_frame,
        fg_color=SAMURAI_PANEL,
        segmented_button_fg_color=SAMURAI_BG,
        segmented_button_selected_color=SAMURAI_RED,
        segmented_button_selected_hover_color=SAMURAI_RED_HOVER
    )
    tabview.pack(fill='both', expand=True, pady=10)
    
    tabview.add("Мотивация")
    tabview.add("Аффирмации")
    tabview.add("Юмор")
    
    # Загружаем содержимое вкладок
    load_quotes_tab(tabview.tab("Мотивация"), Motivation, 'motivation')
    load_quotes_tab(tabview.tab("Аффирмации"), Affirmation, 'affirmation')
    load_quotes_tab(tabview.tab("Юмор"), FunnyQuote, 'funny')
    
    create_samurai_label(main_frame, "* Все изменения сохраняются в свитки знаний", 
                       text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 10)).pack(pady=5)
    
    create_samurai_button(main_frame, "Закрыть", manage_win.destroy).pack(pady=10)

def load_quotes_tab(parent, ModelClass, quote_type):
    """Загрузка вкладки управления цитатами"""
    # Кнопки управления
    btn_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    btn_frame.pack(fill='x', pady=10)
    
    def add_quote():
        add_quote_window(quote_type)
    
    def refresh_quotes():
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            quotes = ModelClass.select()
            for quote in quotes:
                status = "Удалена" if quote.is_deleted else "Активна"
                display_text = quote.text
                if len(display_text) > 80:
                    display_text = display_text[:80] + "..."
                
                tree.insert("", "end", values=(display_text, quote.author, status), tags=(quote.id,))
        except Exception as e:
            logger.error(f"Ошибка загрузки цитат: {e}")
    
    create_samurai_button(btn_frame, "Добавить мудрость", add_quote, width=150).pack(side='left', padx=5)
    create_samurai_button(btn_frame, "Обновить", refresh_quotes, width=100).pack(side='right', padx=5)
    
    # Таблица цитат
    table_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    table_frame.pack(fill='both', expand=True)
    
    columns = ("text", "author", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    tree.heading("text", text="Мудрость")
    tree.heading("author", text="Автор")
    tree.heading("status", text="Статус")
    
    tree.column("text", width=600, anchor="w")
    tree.column("author", width=200, anchor="w")
    tree.column("status", width=100, anchor="w")
    
    # Скроллбар
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # === ИСПРАВЛЕНИЕ СКРОЛЛИНГА ===
    setup_touchpad_scrolling(tree)
    # ==============================

    # Контекстное меню
    context_menu = Menu(root, tearoff=0, bg=SAMURAI_PANEL, fg="white")
    context_menu.add_command(label="Редактировать", command=lambda: edit_selected_quote(tree, quote_type))
    context_menu.add_command(label="Удалить/Скрыть", command=lambda: delete_selected_quote(tree, quote_type))
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)
    tree.bind("<Double-1>", lambda e: edit_selected_quote(tree, quote_type))
    
    # Загружаем данные
    refresh_quotes()

def add_quote_window(quote_type):
    if not is_main_admin():
        messagebox.showerror("Ошибка", "Только главный Сёгун может добавлять мудрость")
        return
    
    add_win = ctk.CTkToplevel(root)
    add_win.title("Новая мудрость")
    add_win.geometry("600x400")
    add_win.configure(fg_color=SAMURAI_BG)
    add_win.transient(root)
    add_win.grab_set()
    
    main_frame = create_samurai_frame(add_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    titles = {
        'motivation': 'Мотивационная цитата',
        'affirmation': 'Аффирмация', 
        'funny': 'Юмористическая цитата'
    }
    
    create_samurai_label(main_frame, f"Добавить {titles[quote_type]}", 
                       font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=10)
    
    create_samurai_label(main_frame, "Мудрость:", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    text_entry = create_samurai_textbox(main_frame, height=100)
    text_entry.pack(fill='x', pady=5)
    
    # Подсказка для автора
    author_label_text = "Автор (оставьте пустым для аффирмаций):" if quote_type == 'affirmation' else "Автор:"
    create_samurai_label(main_frame, author_label_text, text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    
    author_entry = create_samurai_entry(main_frame)
    author_entry.pack(fill='x', pady=5)
    
    def save_quote():
        text = text_entry.get("1.0", "end").strip()
        author = author_entry.get().strip()
        
        if not text:
            messagebox.showerror("Ошибка", "Впишите мудрость")
            return
        
        # --- ИЗМЕНЕНИЕ: ЛОГИКА ПУСТОГО АВТОРА ---
        if not author:
            if quote_type == 'affirmation':
                author = "" # Разрешаем пустоту для аффирмаций
            else:
                author = "Неизвестный" # Для остальных ставим дефолт
        
        try:
            models = {
                'motivation': Motivation,
                'affirmation': Affirmation,
                'funny': FunnyQuote
            }
            model = models[quote_type]
            model.create(text=text, author=author)
            
            # Логируем действие (для летописи)
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='add_quote',
                target_username='System',
                details=f"Добавил {quote_type}: {text[:30]}..."
            )
            
            if update_parser_file():
                messagebox.showinfo("Успех", "Мудрость добавлена в свитки!")
            else:
                messagebox.showinfo("Внимание", "Мудрость добавлена, но ошибка обновления свитков")
            
            add_win.destroy()
            
        except Exception as e:
            logger.error(f"Ошибка добавления: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось добавить мудрость: {str(e)}")
    
    create_samurai_button(main_frame, "Сохранить мудрость", save_quote).pack(pady=20)

def edit_selected_quote(tree, quote_type):
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Выбор", "Выберите мудрость")
        return
    
    item = selection[0]
    quote_id = tree.item(item, "tags")[0]
    
    try:
        models = {
            'motivation': Motivation,
            'affirmation': Affirmation,
            'funny': FunnyQuote
        }
        model = models[quote_type]
        quote = model.get_by_id(quote_id)
        
        edit_win = ctk.CTkToplevel(root)
        edit_win.title("Изменить мудрость")
        edit_win.geometry("600x400")
        edit_win.configure(fg_color=SAMURAI_BG)
        edit_win.transient(root)
        edit_win.grab_set()
        
        main_frame = create_samurai_frame(edit_win, fg_color=SAMURAI_BG)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        create_samurai_label(main_frame, "Изменить мудрость", 
                           font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=10)
        
        create_samurai_label(main_frame, "Мудрость:", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
        text_entry = create_samurai_textbox(main_frame, height=100)
        text_entry.pack(fill='x', pady=5)
        text_entry.insert("1.0", quote.text)
        
        create_samurai_label(main_frame, "Автор:", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
        author_entry = create_samurai_entry(main_frame)
        author_entry.pack(fill='x', pady=5)
        author_entry.insert(0, quote.author)
        
        def update_quote():
            text = text_entry.get("1.0", "end").strip()
            author = author_entry.get().strip()
            
            if not text:
                messagebox.showerror("Ошибка", "Впишите мудрость")
                return
            
            # --- ИЗМЕНЕНИЕ: ЛОГИКА ПУСТОГО АВТОРА ---
            if not author:
                if quote_type == 'affirmation':
                    author = ""
                else:
                    author = "Неизвестный"
            
            try:
                quote.text = text
                quote.author = author
                quote.save()
                
                # Логируем действие
                AdminActionLog.create(
                    admin_username=current_user['username'],
                    action_type='edit_quote',
                    target_username='System',
                    details=f"Изменил {quote_type} ID {quote.id}"
                )
                
                if update_parser_file():
                    messagebox.showinfo("Успех", "Мудрость изменена!")
                else:
                    messagebox.showinfo("Внимание", "Мудрость изменена, но ошибка обновления свитков")
                
                edit_win.destroy()
                
            except Exception as e:
                logger.error(f"Ошибка изменения: {str(e)}")
                messagebox.showerror("Ошибка", f"Не удалось изменить мудрость: {str(e)}")
        
        create_samurai_button(main_frame, "Сохранить изменения", update_quote).pack(pady=20)
        
    except Exception as e:
        logger.error(f"Ошибка редактирования: {str(e)}")
        messagebox.showerror("Ошибка", f"Не удалось загрузить мудрость: {str(e)}")

def delete_selected_quote(tree, quote_type):
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Выбор", "Выберите мудрость")
        return
    
    item = selection[0]
    quote_id = tree.item(item, "tags")[0]
    
    models = {
        'motivation': Motivation,
        'affirmation': Affirmation,
        'funny': FunnyQuote
    }
    model = models[quote_type]
    
    try:
        quote = model.get_by_id(quote_id)
        
        del_win = ctk.CTkToplevel(root)
        del_win.title("Судьба мудрости")
        del_win.geometry("350x200")
        del_win.configure(fg_color=SAMURAI_BG)
        del_win.transient(root)
        del_win.grab_set()
        
        main_frame = create_samurai_frame(del_win, fg_color=SAMURAI_BG)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        create_samurai_label(main_frame, "Как поступить с мудростью?", 
                           font=FONT_BOLD, text_color=SAMURAI_GOLD).pack(pady=10)
        
        create_samurai_label(main_frame, f"\"{quote.text[:30]}...\"", 
                           text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 10, 'italic')).pack(pady=5)
        
        def soft_delete():
            quote.is_deleted = True
            quote.save()
            messagebox.showinfo("Успех", "Мудрость скрыта")
            del_win.destroy()
        
        def hard_delete():
            if messagebox.askyesno("Подтверждение", "Уничтожить мудрость навсегда?"):
                quote.delete_instance()
                update_parser_file()
                messagebox.showinfo("Успех", "Мудрость уничтожена")
                del_win.destroy()
        
        btn_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
        btn_frame.pack(pady=20)
        
        create_samurai_button(
            btn_frame, 
            "Скрыть", 
            soft_delete,
            color=SAMURAI_GOLD,
            hover_color=SAMURAI_GOLD_HOVER
        ).pack(side='left', padx=10)
        
        create_samurai_button(
            btn_frame, 
            "Уничтожить", 
            hard_delete,
            color=SAMURAI_RED,
            hover_color=SAMURAI_RED_HOVER
        ).pack(side='left', padx=10)

    except Exception as e:
        logger.error(f"Ошибка удаления: {e}")

def update_parser_file():
    """Обновление файла parser.py"""
    try:
        motivations_data = []
        affirmations_data = []
        funny_quotes_data = []
        
        for motivation in Motivation.select():
            motivations_data.append({
                "text": motivation.text,
                "author": motivation.author
            })
            
        for affirmation in Affirmation.select():
            affirmations_data.append({
                "text": affirmation.text,
                "author": affirmation.author
            })
            
        for funny_quote in FunnyQuote.select():
            funny_quotes_data.append({
                "text": funny_quote.text,
                "author": funny_quote.author
            })
        
        file_content = f'''from peewee import MySQLDatabase
from connect import Motivation, Affirmation, FunnyQuote, db  

motivations = {json.dumps(motivations_data, ensure_ascii=False, indent=4)}

affirmations = {json.dumps(affirmations_data, ensure_ascii=False, indent=4)}

funny_quotes = {json.dumps(funny_quotes_data, ensure_ascii=False, indent=4)}

def insert_data():
    db.connect()
    try:
        with db.atomic():
            if motivations: Motivation.insert_many(motivations).on_conflict_ignore().execute()
            if affirmations: Affirmation.insert_many(affirmations).on_conflict_ignore().execute()
            if funny_quotes: FunnyQuote.insert_many(funny_quotes).on_conflict_ignore().execute()
        print("Данные успешно вставлены")
    finally:
        db.close()

if __name__ == "__main__":
    insert_data()
'''
        
        with open('parser.py', 'w', encoding='utf-8') as f:
            f.write(file_content)
            
        logger.info("Файл parser.py успешно обновлен")
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении parser.py: {e}")
        return False

def logout():
    global current_user
    current_user = None
    show_auth_window()

# ========== ЗАПУСК ПРИЛОЖЕНИЯ ==========

if __name__ == "__main__":
    init_db()
    show_auth_window()
    root.mainloop()