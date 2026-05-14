import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, Menu, ttk, filedialog
from PIL import Image
import webbrowser
import hashlib
import secrets
import os
import json
import logging
import random
import string
import math
from datetime import datetime

from connect import (
    Avtorization, Motivation, Affirmation, FunnyQuote,
    AdminRequests, UserReaction, UserProfile, AdminActionLog, init_db,
    Category, CategoryQuote, QuoteRating, UserQuoteRating
)


def set_fullscreen(window):
    try:
        if os.name == 'nt':
            window.state('zoomed')
        else:
            window.attributes('-fullscreen', True)
    except Exception as e:
        logging.error(f"Ошибка установки полноэкранного режима: {e}")
        try:
            window.state('zoomed')
        except:
            pass

def toggle_fullscreen(event=None):
    try:
        if os.name == 'nt':
            if root.state() == 'zoomed':
                root.state('normal')
            else:
                root.state('zoomed')
        else:
            if root.attributes('-fullscreen'):
                root.attributes('-fullscreen', False)
            else:
                root.attributes('-fullscreen', True)
    except Exception as e:
        logging.error(f"Ошибка переключения полноэкранного режима: {e}")


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


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


FONT_PRIMARY = ("Segoe UI", 12)
FONT_BOLD = ("Segoe UI", 12, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_HEADER = ("Segoe UI", 16, "bold")


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_errors.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


current_user = None
active_windows = {}


root = ctk.CTk()
root.title('Bushido Motivation System')
root.configure(fg_color=SAMURAI_BG)


set_fullscreen(root)


root.bind('<Escape>', toggle_fullscreen)


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


loading_window = None
loading_progress = None
loading_label = None
loading_canvas = None
loading_frames = []
loading_animation_id = None


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


def setup_touchpad_scrolling(widget):
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

def check_auth():
    global current_user
    if current_user is None:
        show_auth_window()
        return False
    return True


def get_or_create_profile(username):
    try:
        profile = UserProfile.get(UserProfile.username == username)
        return profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.create(username=username, nickname='', avatar_path='')
        return profile

def update_profile(username, nickname=None, avatar_path=None):
    try:
        profile = get_or_create_profile(username)
        if nickname is not None:
            profile.nickname = nickname
        if avatar_path is not None:
            profile.avatar_path = avatar_path
        profile.save()
        return True, "Профиль обновлен"
    except Exception as e:
        logger.error(f"Ошибка обновления профиля: {e}")
        return False, str(e)

def get_display_name(username):
    try:
        profile = UserProfile.get(UserProfile.username == username)
        return profile.nickname if profile.nickname else username
    except UserProfile.DoesNotExist:
        return username

def save_avatar(username, image_path):
    try:
        if not os.path.exists('avatars'):
            os.makedirs('avatars')

        import shutil
        file_ext = os.path.splitext(image_path)[1]
        new_path = f"avatars/{username}{file_ext}"
        shutil.copy2(image_path, new_path)

        update_profile(username, avatar_path=new_path)
        return True, new_path
    except Exception as e:
        logger.error(f"Ошибка сохранения аватарки: {e}")
        return False, str(e)


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
    
    root.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() // 2) - 200
    y = root.winfo_y() + (root.winfo_height() // 2) - 175
    loading_window.geometry(f"+{x}+{y}")
    loading_window.transient(root)
    loading_window.grab_set()
    
    border_frame = create_samurai_frame(loading_window, border_color=SAMURAI_GOLD)
    border_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    create_samurai_label(border_frame, "Медитация...", font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=(25, 10))
    
    animation_frame = create_samurai_frame(border_frame, fg_color=SAMURAI_BG)
    animation_frame.pack(pady=5)
    
    animation_label = ctk.CTkLabel(animation_frame, text="", fg_color=SAMURAI_BG)
    animation_label.pack()
    
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

        if loading_frames and current_frame_index < len(loading_frames):
            animation_label.configure(image=loading_frames[current_frame_index])
            current_frame_index = (current_frame_index + 1) % len(loading_frames)
        
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


def update_nav_user_info(nav_frame):
    
    user_frame = None
    for widget in nav_frame.winfo_children():
        if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") == "transparent":
            
            pack_info = widget.pack_info()
            if pack_info.get('side') == 'right':
                user_frame = widget
                break
    
    if user_frame:
        
        for child in user_frame.winfo_children():
            child.destroy()
        
        display_name = get_display_name(current_user['username'])
        profile = get_or_create_profile(current_user['username'])
        
        
        user_info_container = ctk.CTkFrame(user_frame, fg_color="transparent")
        user_info_container.pack(side='left', padx=10)
        
        
        name_label = create_samurai_label(
            user_info_container, 
            display_name,
            font=FONT_BOLD, 
            text_color=SAMURAI_GOLD
        )
        name_label.pack(side='left')
        
        
        avatar_label = ctk.CTkLabel(user_info_container, text="", width=30, height=30)
        avatar_label.pack(side='left', padx=(5, 0))
        
        if profile.avatar_path and os.path.exists(profile.avatar_path):
            try:
                img = Image.open(profile.avatar_path)
                img = img.resize((30, 30), Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(30, 30))
                avatar_label.configure(image=ctk_image)
                avatar_label.image = ctk_image
            except Exception as e:
                logger.error(f"Ошибка загрузки аватарки в навигации: {e}")
                avatar_label.configure(text="👤", font=("Segoe UI", 16))
        else:
            avatar_label.configure(text="👤", font=("Segoe UI", 16))
        
        
        # Кнопка "Сёгун" только для главного администратора
        if is_main_admin():
            create_samurai_button(
                user_frame, "Сёгун", 
                developer_window,
                color=SAMURAI_RED, 
                width=80
            ).pack(side='left', padx=5)
        
        create_samurai_button(
            user_frame, "Выйти", 
            logout, 
            width=80
        ).pack(side='left', padx=5)
        
        create_samurai_button(
            user_frame, "Профиль", 
            show_profile_settings,
            color=SAMURAI_GREEN, 
            hover_color=SAMURAI_GREEN_HOVER, 
            width=80
        ).pack(side='left', padx=5)

def create_navigation_bar(parent, active_tab=None):
    nav_frame = create_samurai_frame(parent, fg_color="black")
    nav_frame.pack(fill='x', side='top')
    
    
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
    
    
    nav_buttons_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    nav_buttons_frame.pack(side='left', padx=50, pady=10, expand=True)
    
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
    
    create_nav_button("Главная", lambda: show_loading_screen(home_window), active_tab == 'home').pack(side='left', padx=5)
    create_nav_button("Мотивация", lambda: show_loading_screen(motivation_window), active_tab == 'motivation').pack(side='left', padx=5)
    create_nav_button("Аффирмации", lambda: show_loading_screen(affirmation_window), active_tab == 'affirmation').pack(side='left', padx=5)
    create_nav_button("Юмор", lambda: show_loading_screen(funny_quotes_window), active_tab == 'funny').pack(side='left', padx=5)
    create_nav_button("Категории", lambda: show_loading_screen(categories_main_window), active_tab == 'categories').pack(side='left', padx=5)
    
    
    user_frame = create_samurai_frame(nav_frame, fg_color="transparent")
    user_frame.pack(side='right', padx=20, pady=10)
    
    return nav_frame, user_frame


def show_auth_window():
    create_first_admin()
    
    for widget in root.winfo_children():
        widget.destroy()
    
    main_frame = create_samurai_frame(root, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True)
    
    title_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    title_frame.pack(pady=50)
    
    create_samurai_label(title_frame, "Путь Самурая", font=FONT_TITLE, text_color=SAMURAI_GOLD).pack()
    create_samurai_label(title_frame, "Система мотивационных высказываний", 
                        font=FONT_PRIMARY, text_color=SAMURAI_TEXT_SECONDARY).pack(pady=10)
    
    form_container = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    form_container.pack(pady=20)
    
    show_login_form(form_container)

def show_login_form(parent):
    for widget in parent.winfo_children():
        widget.destroy()
    
    login_frame = create_samurai_frame(parent, border_color=SAMURAI_GOLD)
    login_frame.pack(padx=50, pady=20)
    
    create_samurai_label(login_frame, "Вход в Додзё", font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=20)
    
    input_frame = create_samurai_frame(login_frame, fg_color=SAMURAI_BG)
    input_frame.pack(padx=30, pady=10, fill='x')
    
    create_samurai_label(input_frame, "Имя воина", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    username_entry = create_samurai_entry(input_frame, "Введите имя")
    username_entry.pack(fill='x', pady=5)
    
    create_samurai_label(input_frame, "Секретный свиток", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    password_entry = create_samurai_entry(input_frame, "Введите пароль", show="*")
    password_entry.pack(fill='x', pady=5)
    
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

        try:
            user = Avtorization.get(Avtorization.username == username)
            if user.password == hash_password(password):
                global current_user
                current_user = {
                    'username': user.username,
                    'role': user.role
                }
                
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
    
    def switch_to_register():
        show_register_form(parent)
    
    register_link = create_samurai_label(login_frame, "Нет пути? Создать новый", 
                                       text_color=SAMURAI_GOLD, font=('Segoe UI', 10, 'underline'))
    register_link.pack(pady=10)
    register_link.bind("<Button-1>", lambda e: switch_to_register())

def show_register_form(parent):
    for widget in parent.winfo_children():
        widget.destroy()
    
    register_frame = create_samurai_frame(parent, border_color=SAMURAI_GOLD)
    register_frame.pack(padx=50, pady=20)
    
    create_samurai_label(register_frame, "Новый путь", font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=20)
    
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
            
            Avtorization.create(
                username=username,
                password=hash_password(password),
                role='пользователь'
            )
            
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
            first_admin_password = "admin"
            
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

def complete_admin_registration_window(username):
    complete_win = ctk.CTkToplevel(root)
    complete_win.title("Посвящение в Сёгуны")
    complete_win.geometry("500x350")
    complete_win.configure(fg_color=SAMURAI_BG)
    complete_win.transient(root)
    complete_win.grab_set()
    

    set_fullscreen(complete_win)
    
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
    
    info_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    info_frame.pack(pady=10)
    
    create_samurai_label(info_frame, "Токен находится в свитке:", 
                        text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 10, 'bold')).pack()
    
    token_filename = f"tokens/{username}_token.txt"
    create_samurai_label(info_frame, token_filename, 
                        text_color=SAMURAI_GOLD, font=('Segoe UI', 10)).pack()
    
    create_samurai_label(main_frame, "Если свиток утерян, обратитесь к главному Сёгуну",
                        text_color=SAMURAI_RED, font=('Segoe UI', 9)).pack(pady=10)


def show_profile_settings():
    if not check_auth():
        return

    global current_user
    profile_win = ctk.CTkToplevel(root)
    profile_win.title("Настройки профиля")
    profile_win.geometry("650x600")
    profile_win.configure(fg_color=SAMURAI_BG)
    profile_win.transient(root)
    profile_win.grab_set()
    
    
    set_fullscreen(profile_win)

    main_container = ctk.CTkScrollableFrame(profile_win, fg_color=SAMURAI_BG,
                                           border_width=0, corner_radius=0)
    main_container.pack(fill='both', expand=True, padx=20, pady=20)

    create_samurai_label(main_container, "Настройки профиля",
                        font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=10)

    profile = get_or_create_profile(current_user['username'])

    avatar_frame = create_samurai_frame(main_container, fg_color=SAMURAI_PANEL, border_color=SAMURAI_GOLD)
    avatar_frame.pack(fill='x', pady=10)

    create_samurai_label(avatar_frame, "Аватар:",
                        font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w', padx=10, pady=5)

    avatar_display_frame = create_samurai_frame(avatar_frame, fg_color=SAMURAI_BG)
    avatar_display_frame.pack(pady=10)

    avatar_label = ctk.CTkLabel(avatar_display_frame, text="", fg_color=SAMURAI_PANEL)
    avatar_label.pack(pady=5)

    def display_avatar():
        if profile.avatar_path and os.path.exists(profile.avatar_path):
            try:
                img = Image.open(profile.avatar_path)
                img = img.resize((150, 150), Image.Resampling.LANCZOS)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(150, 150))
                avatar_label.configure(image=ctk_image, text="")
                avatar_label.image = ctk_image
            except Exception as e:
                logger.error(f"Ошибка загрузки аватара: {e}")
                avatar_label.configure(text="[Нет аватара]", image=None)
        else:
            avatar_label.configure(text="[Нет аватара]", image=None)

    display_avatar()

    def upload_avatar():
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            success, result = save_avatar(current_user['username'], file_path)
            if success:
                messagebox.showinfo("Успех", "Аватар обновлен")
                nonlocal profile
                profile = get_or_create_profile(current_user['username'])
                display_avatar()
                

                for widget in root.winfo_children():
                    if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") == "black":
                        update_nav_user_info(widget)
                        break
            else:
                messagebox.showerror("Ошибка", f"Не удалось сохранить аватар: {result}")

    create_samurai_button(avatar_frame, "Загрузить аватар", upload_avatar).pack(pady=10)

    nickname_frame = create_samurai_frame(main_container, fg_color=SAMURAI_PANEL, border_color=SAMURAI_GOLD)
    nickname_frame.pack(fill='x', pady=10)

    create_samurai_label(nickname_frame, "Отображаемое имя (никнейм):",
                        font=FONT_BOLD, text_color=SAMURAI_TEXT).pack(anchor='w', padx=10, pady=5)

    create_samurai_label(nickname_frame, "Оставьте пустым для использования логина",
                        text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 9)).pack(anchor='w', padx=10)

    nickname_entry = create_samurai_entry(nickname_frame, width=400)
    nickname_entry.pack(padx=10, pady=10)
    nickname_entry.insert(0, profile.nickname if profile.nickname else "")

    buttons_frame = create_samurai_frame(main_container, fg_color=SAMURAI_BG)
    buttons_frame.pack(pady=20)

    def save_changes():
        new_nickname = nickname_entry.get().strip()
        success, message = update_profile(current_user['username'], nickname=new_nickname)
        if success:
            messagebox.showinfo("Успех", "Профиль обновлен")
            profile_win.destroy()
            
            for widget in root.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") == "black":
                    update_nav_user_info(widget)
                    break
        else:
            messagebox.showerror("Ошибка", message)

    create_samurai_button(buttons_frame, "Сохранить", save_changes,
                         color=SAMURAI_GREEN, hover_color=SAMURAI_GREEN_HOVER).pack(side='left', padx=10)

    create_samurai_button(buttons_frame, "Отмена", profile_win.destroy,
                         color=SAMURAI_PANEL, hover_color="#333").pack(side='left', padx=10)


# ========== КЛАСС ДЛЯ РЕЙТИНГА ==========

class RatingManager:
    """Менеджер для работы с рейтингами цитат"""
    
    def __init__(self, username):
        self.username = username
    
    def get_quote_rating(self, quote_id, quote_type):
        """Получить средний рейтинг цитаты"""
        try:
            rating = QuoteRating.get_or_none(
                (QuoteRating.quote_id == quote_id) &
                (QuoteRating.quote_type == quote_type)
            )
            if rating:
                return {
                    'average': rating.average_rating,
                    'votes': rating.votes_count,
                    'total': rating.total_rating
                }
            return {'average': 0, 'votes': 0, 'total': 0}
        except Exception as e:
            logger.error(f"Ошибка получения рейтинга: {e}")
            return {'average': 0, 'votes': 0, 'total': 0}
    
    def get_top_rated_quotes(self, quote_type=None, limit=10, min_votes=1):
        """Получить топ цитат по рейтингу"""
        try:
            query = QuoteRating.select().where(
                QuoteRating.votes_count >= min_votes
            ).order_by(QuoteRating.average_rating.desc()).limit(limit)
            
            if quote_type:
                query = query.where(QuoteRating.quote_type == quote_type)
            
            results = []
            models = {
                'motivation': Motivation,
                'affirmation': Affirmation,
                'funny': FunnyQuote
            }
            
            for rating in query:
                model = models.get(rating.quote_type)
                if model:
                    try:
                        quote = model.get_by_id(rating.quote_id)
                        if not quote.is_deleted:
                            results.append({
                                'id': quote.id,
                                'type': rating.quote_type,
                                'text': quote.text,
                                'author': quote.author,
                                'rating': rating.average_rating,
                                'votes': rating.votes_count
                            })
                    except:
                        pass
            return results
        except Exception as e:
            logger.error(f"Ошибка получения топа: {e}")
            return []


# ========== ВИДЖЕТ ДЛЯ ОТОБРАЖЕНИЯ РЕЙТИНГА С ЧАСТИЧНЫМ ЗАПОЛНЕНИЕМ ЗВЕЗД ==========

class RatingDisplayWidget(ctk.CTkFrame):
    """Виджет для отображения рейтинга звездами с частичным заполнением (как на HDRezka)"""
    
    def __init__(self, parent, rating_info, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.rating_info = rating_info
        self.setup_ui()
    
    def setup_ui(self):
        avg = self.rating_info.get('average', 0)
        votes = self.rating_info.get('votes', 0)
        
        # Отображаем звезды с частичным заполнением
        stars_frame = ctk.CTkFrame(self, fg_color="transparent")
        stars_frame.pack(side='left', padx=5)
        
        # Создаем 5 звезд с частичным заполнением
        star_size = 20
        star_padding = 2
        
        for i in range(5):
            star_number = i + 1
            
            # Вычисляем процент заполнения для текущей звезды (0.0 до 1.0)
            if avg >= star_number:
                fill_percent = 1.0  # Полностью заполнена
            elif avg > star_number - 1:
                fill_percent = avg - (star_number - 1)  # Частично заполнена
            else:
                fill_percent = 0.0  # Пустая
            
            # Создаем canvas для одной звезды
            star_canvas = tk.Canvas(
                stars_frame, 
                width=star_size + star_padding * 2, 
                height=star_size + star_padding * 2, 
                bg=SAMURAI_BG, 
                highlightthickness=0
            )
            star_canvas.pack(side='left', padx=0)
            
            # Рисуем звезду с частичным заполнением
            self.draw_partial_star(star_canvas, star_size, star_padding, fill_percent)
        
        # Числовое значение и количество голосов
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side='left', padx=10)
        
        if votes > 0:
            rating_text = f"{avg:.1f} ({votes} голосов)"
            rating_color = SAMURAI_GOLD
        else:
            rating_text = "Нет оценок"
            rating_color = SAMURAI_TEXT_SECONDARY
        
        ctk.CTkLabel(
            info_frame, 
            text=rating_text, 
            font=FONT_PRIMARY, 
            text_color=rating_color
        ).pack(side='left')
    
    def draw_partial_star(self, canvas, size, padding, fill_percent):
        """Рисует звезду с частичным заполнением"""
        cx = size / 2 + padding
        cy = size / 2 + padding
        r = size / 2 - 1
        
        # Вычисляем точки звезды
        points = []
        for i in range(10):
            angle = math.pi / 2 - i * math.pi / 5
            if i % 2 == 0:
                radius = r
            else:
                radius = r * 0.4
            
            x = cx + radius * math.cos(angle)
            y = cy - radius * math.sin(angle)
            points.extend([x, y])
        
        # Рисуем контур звезды (пустая звезда)
        canvas.create_polygon(points, fill=SAMURAI_BG, outline=SAMURAI_TEXT_SECONDARY, width=1)
        
        if fill_percent > 0:
            # Создаем маску для частичного заполнения
            clip_width = int((size + padding * 2) * fill_percent)
            
            # Рисуем заполненную часть звезды золотым цветом
            if fill_percent >= 1.0:
                # Полностью заполненная звезда
                canvas.create_polygon(points, fill=SAMURAI_GOLD, outline=SAMURAI_GOLD)
            else:
                # Частично заполненная звезда
                # Сначала рисуем золотую звезду
                star_id = canvas.create_polygon(points, fill=SAMURAI_GOLD, outline=SAMURAI_GOLD)
                
                # Затем рисуем прямоугольник фона, который обрезает звезду справа
                clip_id = canvas.create_rectangle(
                    clip_width, 0, 
                    size + padding * 2 + 10, size + padding * 2 + 10,
                    fill=SAMURAI_BG, outline=''
                )
                
                # Поднимаем обрезающий прямоугольник над звездой
                canvas.tag_raise(clip_id, star_id)


# ========== ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ ТОПА ==========

def show_top_quotes_window(rating_manager, quote_filter=None):
    """Показать окно с топ-цитатами"""
    top_win = ctk.CTkToplevel(root)
    top_win.title("🏆 Топ цитат")
    top_win.geometry("800x600")
    top_win.configure(fg_color=SAMURAI_BG)
    top_win.transient(root)
    top_win.grab_set()
    
    set_fullscreen(top_win)
    
    main_frame = create_samurai_frame(top_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, "🏆 Топ цитат по рейтингу", font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=10)
    
    scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color=SAMURAI_BG)
    scroll_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    type_labels = {'motivation': '💪 Мотивация', 'affirmation': '🌸 Аффирмация', 'funny': '😄 Юмор'}
    types_to_show = [quote_filter] if quote_filter else ['motivation', 'affirmation', 'funny']
    
    for quote_type in types_to_show:
        top_quotes = rating_manager.get_top_rated_quotes(quote_type, limit=20, min_votes=1)
        
        type_frame = create_samurai_frame(scroll_frame, border_color=SAMURAI_GOLD)
        type_frame.pack(fill='x', pady=10)
        
        create_samurai_label(type_frame, type_labels.get(quote_type, quote_type), 
                            font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(anchor='w', padx=10, pady=5)
        
        if top_quotes:
            for i, q in enumerate(top_quotes, 1):
                quote_frame = create_samurai_frame(type_frame, fg_color=SAMURAI_PANEL)
                quote_frame.pack(fill='x', padx=10, pady=5)
                
                header_frame = ctk.CTkFrame(quote_frame, fg_color="transparent")
                header_frame.pack(fill='x')
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                create_samurai_label(header_frame, f"{medal}", font=FONT_BOLD, 
                                    text_color=SAMURAI_GOLD).pack(side='left', padx=5)
                
                RatingDisplayWidget(header_frame, {'average': q['rating'], 'votes': q['votes']}).pack(side='left', padx=10)
                
                text_preview = q['text'][:100] + "..." if len(q['text']) > 100 else q['text']
                create_samurai_label(quote_frame, f"«{text_preview}»",
                                    font=('Georgia', 11, 'italic'), text_color=SAMURAI_TEXT, 
                                    wraplength=700, justify='left').pack(anchor='w', padx=10, pady=5)
                
                if q['author']:
                    create_samurai_label(quote_frame, f"— {q['author']}", 
                                        font=('Segoe UI', 10), text_color=SAMURAI_TEXT_SECONDARY).pack(anchor='w', padx=10, pady=(0, 5))
        else:
            create_samurai_label(type_frame, "Нет оцененных цитат", 
                                text_color=SAMURAI_TEXT_SECONDARY).pack(pady=10)
    
    create_samurai_button(main_frame, "Закрыть", top_win.destroy).pack(pady=10)


def home_window():
    if not check_auth():
        return
        
    for widget in root.winfo_children():
        widget.destroy()
    
    
    set_fullscreen(root)
    
    nav_frame, user_frame = create_navigation_bar(root, active_tab='home')
    update_nav_user_info(nav_frame)
    
    separator = ctk.CTkFrame(root, height=2, fg_color=SAMURAI_GOLD, corner_radius=0)
    separator.pack(fill='x', side='top')
    
    main_scroll_frame = ctk.CTkScrollableFrame(
        root,
        fg_color=SAMURAI_BG,
        scrollbar_button_color=SAMURAI_RED,
        scrollbar_button_hover_color=SAMURAI_RED_HOVER,
        scrollbar_fg_color=SAMURAI_PANEL,
        corner_radius=0,
        label_fg_color=SAMURAI_BG
    )
    main_scroll_frame.pack(fill='both', expand=True, padx=0, pady=0)
    
    center_container = create_samurai_frame(main_scroll_frame, fg_color=SAMURAI_BG)
    center_container.pack(expand=True, fill='both', padx=30, pady=20)
    
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
    
    social_frame = create_samurai_frame(center_container, fg_color=SAMURAI_BG)
    social_frame.pack(pady=20)

    def open_link(url):
        webbrowser.open_new(url)

    def create_social_button(image_path, url, size=50):
        try:
            if os.path.exists(image_path):
                img = Image.open(image_path)
                ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
                
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

    ctk.CTkLabel(center_container, text="", height=100, fg_color=SAMURAI_BG).pack()


def motivation_window():
    show_quote_window('motivation', 'Мотивационные цитаты', Motivation, active_tab='motivation')

def affirmation_window():
    show_quote_window('affirmation', 'Аффирмации', Affirmation, active_tab='affirmation')

def funny_quotes_window():
    show_quote_window('funny', 'Смешные цитаты', FunnyQuote, active_tab='funny')

def show_quote_window(quote_type, title, ModelClass, active_tab=None):
    if not check_auth():
        return
        
    for widget in root.winfo_children():
        widget.destroy()
    
    
    set_fullscreen(root)
    
    nav_frame, user_frame = create_navigation_bar(root, active_tab=active_tab)
    update_nav_user_info(nav_frame)
    
    separator = ctk.CTkFrame(root, height=2, fg_color=SAMURAI_GOLD, corner_radius=0)
    separator.pack(fill='x', side='top', pady=(0, 10))
    
    content_frame = ctk.CTkFrame(root, fg_color=SAMURAI_BG)
    content_frame.pack(fill='both', expand=True)
    
    # Кнопка для просмотра топа
    top_btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    top_btn_frame.pack(fill='x', padx=20, pady=10)
    
    def show_top():
        rating_manager = RatingManager(current_user['username'])
        show_top_quotes_window(rating_manager, quote_type)
    
    create_samurai_button(
        top_btn_frame,
        "🏆 Топ цитат",
        show_top,
        color=SAMURAI_GOLD,
        hover_color=SAMURAI_GOLD_HOVER,
        width=120
    ).pack(side='right')
    
    create_samurai_label(content_frame, title, font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=20)
    
    disliked_ids = [
        r.quote_id for r in UserReaction.select().where(
            (UserReaction.username == current_user['username']) &
            (UserReaction.quote_type == quote_type) &
            (UserReaction.reaction == 'dislike')
        )
    ]
    
    try:
        all_quotes = ModelClass.select().where(ModelClass.is_deleted == False)
        quotes = [q for q in all_quotes if q.id not in disliked_ids]
        
        if not quotes:
            create_samurai_label(content_frame, "Нет цитат в базе данных", 
                               text_color=SAMURAI_TEXT_SECONDARY).pack(pady=50)
            return
            
        current_quote_index = 0
        
        slider_frame = create_samurai_frame(content_frame, fg_color=SAMURAI_BG)
        slider_frame.pack(pady=10, padx=50, fill='both', expand=True)
        
        quote_card = create_samurai_frame(slider_frame, border_color=SAMURAI_GOLD, height=400)
        quote_card.pack(pady=10, fill='x')
        quote_card.pack_propagate(False)
        
        quote_text_frame = create_samurai_frame(quote_card, fg_color=SAMURAI_CARD)
        quote_text_frame.pack(expand=True, fill='both', padx=30, pady=20)
        
        quote_label = create_samurai_label(
            quote_text_frame, text="", font=("Georgia", 18, "italic"),
            text_color="white", wraplength=800, justify='center'
        )
        quote_label.pack(expand=True)
        
        author_label = create_samurai_label(quote_text_frame, text="", font=FONT_PRIMARY, text_color=SAMURAI_GOLD)
        author_label.pack(pady=(20, 0))
        
        # Фрейм для отображения рейтинга
        rating_frame = ctk.CTkFrame(quote_card, fg_color="transparent")
        rating_frame.pack(fill='x', padx=20, pady=10)
        
        reaction_frame = create_samurai_frame(slider_frame, fg_color=SAMURAI_BG)
        reaction_frame.pack(pady=10)
        
        likes_count_label = create_samurai_label(
            reaction_frame, text="Честь: 0", font=FONT_BOLD, text_color=SAMURAI_GREEN
        )
        likes_count_label.pack(side='left', padx=20)
        
        def update_rating_display():
            if not quotes:
                return
            quote = quotes[current_quote_index]
            
            # Получаем данные о рейтинге из БД (средняя оценка всех пользователей)
            try:
                rating = QuoteRating.get_or_none(
                    (QuoteRating.quote_id == quote.id) & 
                    (QuoteRating.quote_type == quote_type)
                )
                if rating:
                    rating_info = {
                        'average': rating.average_rating,
                        'votes': rating.votes_count
                    }
                else:
                    rating_info = {'average': 0, 'votes': 0}
            except:
                rating_info = {'average': 0, 'votes': 0}
            
            # Очищаем фрейм рейтинга
            for w in rating_frame.winfo_children():
                w.destroy()
            
            # Отображаем виджет с частично заполненными звездами
            RatingDisplayWidget(rating_frame, rating_info).pack(pady=5)
        
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
                update_rating_display()
        
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
                        quote_label.configure(text="Все цитаты отклонены")
                        author_label.configure(text="")
                        return
                    if current_quote_index >= len(quotes):
                        current_quote_index = 0
                    update_quote_display()
                else:
                    update_likes_count()
            except Exception as e:
                logger.error(f"Ошибка при установке реакции: {e}")

        reaction_buttons_frame = create_samurai_frame(reaction_frame, fg_color=SAMURAI_BG)
        reaction_buttons_frame.pack(side='right')
        
        create_samurai_button(reaction_buttons_frame, "👍 Честь", lambda: set_reaction('like'),
                             color=SAMURAI_GREEN, hover_color=SAMURAI_GREEN_HOVER, width=100).pack(side='left', padx=5)
        create_samurai_button(reaction_buttons_frame, "👎 Бесчестие", lambda: set_reaction('dislike'),
                             color=SAMURAI_RED, hover_color=SAMURAI_RED_HOVER, width=100).pack(side='left', padx=5)
        
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

        create_samurai_button(nav_controls_frame, "<", prev_quote, width=50, height=40,
                             font=("Arial", 16, "bold")).pack(side='left', padx=20)
        
        counter_label = create_samurai_label(nav_controls_frame, text="0 / 0",
                                            font=("Segoe UI", 16, "bold"), text_color=SAMURAI_GOLD)
        counter_label.pack(side='left', padx=20)
        
        create_samurai_button(nav_controls_frame, ">", next_quote, width=50, height=40,
                             font=("Arial", 16, "bold")).pack(side='left', padx=20)
        
        create_samurai_button(slider_frame, "🎲 Случайная мудрость", show_random_quote,
                             color=SAMURAI_PANEL, hover_color="#333", width=200).pack(pady=(0, 20))
        
        update_quote_display()
        
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        create_samurai_label(content_frame, "Ошибка загрузки свитков", text_color=SAMURAI_RED).pack()


def add_manual_quote_to_category(category, refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может добавлять цитаты")
        return
    
    add_win = ctk.CTkToplevel(root)
    add_win.title("Добавить цитату вручную")
    add_win.geometry("600x550")
    add_win.configure(fg_color=SAMURAI_BG)
    add_win.transient(root)
    add_win.grab_set()
    
    
    set_fullscreen(add_win)
    
    main_frame = create_samurai_frame(add_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, f"Добавить цитату в категорию: {category.name}", 
                        font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=10)
    
    
    create_samurai_label(main_frame, "Тип цитаты:", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    quote_type_var = ctk.StringVar(value="motivation")
    
    type_frame = create_samurai_frame(main_frame, fg_color="transparent")
    type_frame.pack(fill='x', pady=5)
    
    types = [
        ("Мотивация", "motivation"),
        ("Аффирмация", "affirmation"),
        ("Юмор", "funny")
    ]
    
    for text, value in types:
        rb = ctk.CTkRadioButton(
            type_frame,
            text=text,
            variable=quote_type_var,
            value=value,
            fg_color=SAMURAI_RED,
            text_color=SAMURAI_TEXT
        )
        rb.pack(side='left', padx=10)
    
    
    create_samurai_label(main_frame, "Текст цитаты:", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    text_entry = create_samurai_textbox(main_frame, height=150)
    text_entry.pack(fill='x', pady=5)
    
    
    create_samurai_label(main_frame, "Автор:", text_color=SAMURAI_TEXT).pack(anchor='w', pady=(10, 5))
    author_entry = create_samurai_entry(main_frame, width=400)
    author_entry.pack(fill='x', pady=5)
    
    
    add_to_main_var = ctk.BooleanVar(value=True)
    add_to_main_check = ctk.CTkCheckBox(
        main_frame,
        text="Также добавить в общую таблицу цитат (для отображения в основных разделах)",
        variable=add_to_main_var,
        fg_color=SAMURAI_RED,
        hover_color=SAMURAI_RED_HOVER,
        text_color=SAMURAI_TEXT
    )
    add_to_main_check.pack(pady=10)
    
    def save_manual_quote():
        quote_text = text_entry.get("1.0", "end").strip()
        author = author_entry.get().strip()
        quote_type = quote_type_var.get()
        add_to_main = add_to_main_var.get()
        
        if not quote_text:
            messagebox.showerror("Ошибка", "Введите текст цитаты")
            return
        
        if not author:
            if quote_type == 'affirmation':
                author = ""
            else:
                author = "Неизвестный"
        
        try:
            
            existing = CategoryQuote.select().where(
                (CategoryQuote.category == category.id) &
                (CategoryQuote.quote_text == quote_text)
            ).first()
            
            if existing:
                messagebox.showerror("Ошибка", "Такая цитата уже есть в этой категории")
                return
            
            
            if add_to_main:
                models = {
                    'motivation': Motivation,
                    'affirmation': Affirmation,
                    'funny': FunnyQuote
                }
                model = models[quote_type]
                
                
                try:
                    existing_main = model.get(model.text == quote_text)
                    
                    logger.info(f"Цитата уже существует в общей таблице, ID: {existing_main.id}")
                except model.DoesNotExist:
                    
                    model.create(
                        text=quote_text,
                        author=author
                    )
                    logger.info(f"Создана новая цитата в общей таблице")
            
            
            # ИЗМЕНЕНИЕ: Добавляем информацию о том, кто добавил цитату
            CategoryQuote.create(
                category=category.id,
                quote_type=quote_type,
                quote_text=quote_text,
                quote_author=author,
                added_by=current_user['username']  # Добавляем имя пользователя, который добавил цитату
            )
            
            
            update_parser_file()
            
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='add_manual_quote_to_category',
                target_username='System',
                details=f"Ручное добавление цитаты в категорию {category.name} пользователем {current_user['username']}"
            )
            
            messagebox.showinfo("Успех", "Цитата добавлена в категорию" + 
                              (" и в общую таблицу" if add_to_main else ""))
            add_win.destroy()
            refresh_callback()  
            
        except Exception as e:
            logger.error(f"Ошибка ручного добавления цитаты: {e}")
            messagebox.showerror("Ошибка", f"Не удалось добавить цитату: {str(e)}")
    
    btn_frame = create_samurai_frame(main_frame, fg_color="transparent")
    btn_frame.pack(fill='x', pady=20)
    
    create_samurai_button(
        btn_frame,
        "💾 Сохранить",
        save_manual_quote,
        color=SAMURAI_GREEN,
        hover_color=SAMURAI_GREEN_HOVER,
        width=150
    ).pack(side='left', padx=10)
    
    create_samurai_button(
        btn_frame,
        "✖ Отмена",
        add_win.destroy,
        color=SAMURAI_RED,
        hover_color=SAMURAI_RED_HOVER,
        width=150
    ).pack(side='right', padx=10)


def hard_delete_category(category, refresh_callback):
    if not is_main_admin():
        messagebox.showerror("Ошибка", "Только главный Сёгун может полностью удалять категории")
        return
    
    
    quotes_count = CategoryQuote.select().where(CategoryQuote.category == category.id).count()
    
    if messagebox.askyesno("Подтверждение", 
                          f"⚠️ ПОЛНОЕ УДАЛЕНИЕ ИЗ БД ⚠️\n\n"
                          f"Вы уверены, что хотите навсегда удалить категорию '{category.name}'?\n\n"
                          f"Цитат в категории: {quotes_count}\n\n"
                          f"Это действие НЕЛЬЗЯ ОТМЕНИТЬ! Все связи с цитатами будут удалены."):
        try:
            
            deleted_quotes = CategoryQuote.delete().where(CategoryQuote.category == category.id).execute()
            
            
            category_id = category.id
            category_name = category.name
            category.delete_instance()  
            
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='hard_delete_category',
                target_username='System',
                details=f"Полностью удалена категория: {category_name} (ID: {category_id}), удалено цитат: {deleted_quotes}"
            )
            
            messagebox.showinfo("Успех", 
                              f"Категория '{category_name}' полностью удалена из БД\n"
                              f"Удалено цитат из категории: {deleted_quotes}")
            refresh_callback()  
            
        except Exception as e:
            logger.error(f"Ошибка полного удаления категории: {e}")
            messagebox.showerror("Ошибка", f"Не удалось полностью удалить категорию: {str(e)}")


def soft_delete_category(category, refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может скрывать категории")
        return
    
    
    quotes_count = CategoryQuote.select().where(CategoryQuote.category == category.id).count()
    if quotes_count > 0:
        messagebox.showerror("Ошибка", 
                           f"Нельзя скрыть категорию с цитатами.\n"
                           f"Сначала удалите все цитаты из категории (сейчас: {quotes_count} цитат).")
        return
    
    if messagebox.askyesno("Подтверждение", 
                          f"Вы уверены, что хотите скрыть категорию '{category.name}'?\n\n"
                          f"Категория будет помечена как удаленная, но останется в БД.\n"
                          f"Полное удаление доступно только главному Сёгуну."):
        try:
            
            category.is_deleted = True
            category.save()
            
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='soft_delete_category',
                target_username='System',
                details=f"Скрыта категория: {category.name} (ID: {category.id})"
            )
            
            messagebox.showinfo("Успех", f"Категория '{category.name}' скрыта")
            refresh_callback()  
            
        except Exception as e:
            logger.error(f"Ошибка скрытия категории: {e}")
            messagebox.showerror("Ошибка", f"Не удалось скрыть категорию: {str(e)}")


def restore_category(category, refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может восстанавливать категории")
        return
    
    if messagebox.askyesno("Подтверждение", 
                          f"Восстановить категорию '{category.name}'?"):
        try:
            category.is_deleted = False
            category.save()
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='restore_category',
                target_username='System',
                details=f"Восстановлена категория: {category.name}"
            )
            
            messagebox.showinfo("Успех", f"Категория '{category.name}' восстановлена")
            refresh_callback()
            
        except Exception as e:
            logger.error(f"Ошибка восстановления категории: {e}")
            messagebox.showerror("Ошибка", f"Не удалось восстановить категорию: {str(e)}")


def categories_main_window():
    if not check_auth():
        return
        
    for widget in root.winfo_children():
        widget.destroy()
    
    
    set_fullscreen(root)
    
    nav_frame, user_frame = create_navigation_bar(root, active_tab='categories')
    update_nav_user_info(nav_frame)
    
    separator = ctk.CTkFrame(root, height=2, fg_color=SAMURAI_GOLD, corner_radius=0)
    separator.pack(fill='x', side='top', pady=(0, 10))
    
    
    main_container = ctk.CTkScrollableFrame(
        root, 
        fg_color=SAMURAI_BG,
        scrollbar_button_color=SAMURAI_RED,
        scrollbar_button_hover_color=SAMURAI_RED_HOVER
    )
    main_container.pack(fill='both', expand=True, padx=20, pady=20)
    
    
    header_frame = create_samurai_frame(main_container, fg_color=SAMURAI_BG)
    header_frame.pack(fill='x', pady=(0, 20))
    
    create_samurai_label(header_frame, "Категории мудрости", 
                        font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(side='left')
    
    
    if current_user['role'] == 'администратор':
        add_btn = create_samurai_button(
            header_frame,
            "➕ Создать категорию",
            lambda: add_category_window(refresh_callback=lambda: load_categories()),
            color=SAMURAI_GREEN,
            hover_color=SAMURAI_GREEN_HOVER,
            width=180
        )
        add_btn.pack(side='right', padx=10)
    
    
    filter_frame = create_samurai_frame(main_container, fg_color=SAMURAI_PANEL)
    filter_frame.pack(fill='x', pady=10)
    
    
    search_frame = create_samurai_frame(filter_frame, fg_color="transparent")
    search_frame.pack(fill='x', padx=10, pady=5)
    
    create_samurai_label(search_frame, "🔍 Поиск:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    search_entry = create_samurai_entry(search_frame, width=300)
    search_entry.pack(side='left', padx=5)
    
    
    sort_frame = create_samurai_frame(filter_frame, fg_color="transparent")
    sort_frame.pack(fill='x', padx=10, pady=5)
    
    create_samurai_label(sort_frame, "Сортировка:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    sort_var = ctk.StringVar(value="name_asc")
    
    sort_options = [
        ("По имени (А→Я)", "name_asc"),
        ("По имени (Я→А)", "name_desc"),
        ("Сначала новые", "date_desc"),
        ("Сначала старые", "date_asc"),
        ("По количеству цитат", "quotes_desc")
    ]
    
    sort_combo = ctk.CTkComboBox(
        sort_frame,
        values=[opt[0] for opt in sort_options],
        fg_color=SAMURAI_PANEL,
        border_color=SAMURAI_GOLD,
        button_color=SAMURAI_RED,
        button_hover_color=SAMURAI_RED_HOVER,
        dropdown_fg_color=SAMURAI_PANEL,
        dropdown_hover_color=SAMURAI_RED,
        width=200
    )
    sort_combo.pack(side='left', padx=5)
    sort_combo.set("По имени (А→Я)")
    
    
    filter_status_frame = create_samurai_frame(filter_frame, fg_color="transparent")
    filter_status_frame.pack(fill='x', padx=10, pady=5)
    
    create_samurai_label(filter_status_frame, "Статус:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    status_var = ctk.StringVar(value="all")
    
    ctk.CTkRadioButton(
        filter_status_frame,
        text="Все",
        variable=status_var,
        value="all",
        command=lambda: load_categories(),
        fg_color=SAMURAI_RED,
        text_color=SAMURAI_TEXT
    ).pack(side='left', padx=10)
    
    ctk.CTkRadioButton(
        filter_status_frame,
        text="Активные",
        variable=status_var,
        value="active",
        command=lambda: load_categories(),
        fg_color=SAMURAI_RED,
        text_color=SAMURAI_TEXT
    ).pack(side='left', padx=10)
    
    ctk.CTkRadioButton(
        filter_status_frame,
        text="Скрытые",
        variable=status_var,
        value="deleted",
        command=lambda: load_categories(),
        fg_color=SAMURAI_RED,
        text_color=SAMURAI_TEXT
    ).pack(side='left', padx=10)
    
    def apply_filters():
        load_categories()
    
    create_samurai_button(
        filter_frame,
        "🔍 Применить",
        apply_filters,
        width=100
    ).pack(pady=10)
    
    create_samurai_button(
        filter_frame,
        "🔄 Сбросить",
        lambda: [search_entry.delete(0, 'end'), 
                sort_combo.set("По имени (А→Я)"),
                status_var.set("all"),
                load_categories()],
        width=100
    ).pack(pady=10)
    
    
    categories_container = create_samurai_frame(main_container, fg_color=SAMURAI_BG)
    categories_container.pack(fill='both', expand=True)
    
    def load_categories():
        # Полная очистка контейнера перед загрузкой
        for widget in categories_container.winfo_children():
            widget.destroy()
        
        # Принудительное обновление интерфейса
        categories_container.update_idletasks()
        
        try:
            query = Category.select()
            
            if status_var.get() == "active":
                query = query.where(Category.is_deleted == False)
            elif status_var.get() == "deleted":
                query = query.where(Category.is_deleted == True)
            
            search_text = search_entry.get().strip()
            if search_text:
                query = query.where(
                    (Category.name.contains(search_text)) | 
                    (Category.description.contains(search_text))
                )
            
            sort_option = sort_combo.get()
            sort_map = {
                "По имени (А→Я)": Category.name.asc(),
                "По имени (Я→А)": Category.name.desc(),
                "Сначала новые": Category.created_at.desc(),
                "Сначала старые": Category.created_at.asc()
            }
            
            if sort_option in sort_map:
                query = query.order_by(sort_map[sort_option])
            
            categories = list(query)
            
            if sort_option == "По количеству цитат":
                categories.sort(key=lambda c: CategoryQuote.select().where(
                    CategoryQuote.category == c.id
                ).count(), reverse=True)
            
            if not categories:
                no_cat_frame = create_samurai_frame(categories_container, border_color=SAMURAI_GOLD)
                no_cat_frame.pack(fill='x', pady=20)
                
                create_samurai_label(
                    no_cat_frame, 
                    "Нет категорий, соответствующих фильтрам", 
                    text_color=SAMURAI_TEXT_SECONDARY
                ).pack(pady=50)
                return
            
            for category in categories:
                quotes_count = CategoryQuote.select().where(
                    CategoryQuote.category == category.id
                ).count()
                
                cat_card = create_samurai_frame(categories_container, border_color=SAMURAI_GOLD)
                cat_card.pack(fill='x', pady=10)
                
                header_frame = create_samurai_frame(cat_card, fg_color=SAMURAI_PANEL)
                header_frame.pack(fill='x', padx=10, pady=10)
                
                info_frame = create_samurai_frame(header_frame, fg_color="transparent")
                info_frame.pack(side='left', fill='x', expand=True)
                
                status_text = " [СКРЫТА]" if category.is_deleted else ""
                
                # ИЗМЕНЕНИЕ: Показываем имя создателя категории для главного администратора
                creator_info = ""
                if is_main_admin() and hasattr(category, 'created_by') and category.created_by:
                    creator_info = f" | Создал: {category.created_by}"
                
                create_samurai_label(
                    info_frame,
                    f"📁 {category.name}{status_text}",
                    font=FONT_HEADER,
                    text_color=SAMURAI_GOLD if not category.is_deleted else SAMURAI_RED
                ).pack(anchor='w')
                
                if category.description:
                    create_samurai_label(
                        info_frame,
                        category.description,
                        font=('Segoe UI', 10),
                        text_color=SAMURAI_TEXT_SECONDARY
                    ).pack(anchor='w')
                
                create_samurai_label(
                    info_frame,
                    f"Цитат: {quotes_count} | Создана: {category.created_at.strftime('%d.%m.%Y')}{creator_info}",
                    font=FONT_PRIMARY,
                    text_color=SAMURAI_TEXT
                ).pack(anchor='w', pady=(5, 0))
                
                if current_user['role'] == 'администратор':
                    btn_frame = create_samurai_frame(header_frame, fg_color="transparent")
                    btn_frame.pack(side='right', padx=5)
                    
                    manage_btn = create_samurai_button(
                        btn_frame,
                        "⚙️ Управлять",
                        lambda c=category: manage_category_quotes_window(c, refresh_callback=lambda: load_categories()),
                        width=100,
                        height=30
                    )
                    manage_btn.pack(side='left', padx=2)
                    
                    if not category.is_deleted:
                        hide_btn = create_samurai_button(
                            btn_frame,
                            "👻 Скрыть",
                            lambda c=category: soft_delete_category(c, refresh_callback=lambda: load_categories()),
                            width=80,
                            height=30,
                            color=SAMURAI_RED if quotes_count == 0 else SAMURAI_PANEL
                        )
                        hide_btn.pack(side='left', padx=2)
                        if quotes_count > 0:
                            hide_btn.configure(state="disabled")
                        
                        if is_main_admin():
                            delete_btn = create_samurai_button(
                                btn_frame,
                                "💀 Удалить",
                                lambda c=category: hard_delete_category(c, refresh_callback=lambda: load_categories()),
                                width=80,
                                height=30,
                                color=SAMURAI_RED,
                                hover_color=SAMURAI_RED_HOVER
                            )
                            delete_btn.pack(side='left', padx=2)
                    else:
                        restore_btn = create_samurai_button(
                            btn_frame,
                            "🔄 Восстановить",
                            lambda c=category: restore_category(c, refresh_callback=lambda: load_categories()),
                            width=100,
                            height=30,
                            color=SAMURAI_GREEN,
                            hover_color=SAMURAI_GREEN_HOVER
                        )
                        restore_btn.pack(side='left', padx=2)
                
                view_btn = create_samurai_button(
                    cat_card,
                    "📖 Просмотреть цитаты",
                    lambda c=category: show_category_quotes_window(c),
                    width=200
                )
                view_btn.pack(pady=10)
        
        except Exception as e:
            logger.error(f"Ошибка загрузки категорий: {e}")
            create_samurai_label(
                categories_container,
                f"Ошибка загрузки категорий: {str(e)}",
                text_color=SAMURAI_RED
            ).pack(pady=50)
    
    load_categories()
    
    search_entry.bind("<Return>", lambda e: load_categories())


def add_category_window(refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может создавать категории")
        return
    
    add_win = ctk.CTkToplevel(root)
    add_win.title("Новая категория")
    add_win.geometry("500x400")
    add_win.resizable(False, False)
    add_win.configure(fg_color=SAMURAI_BG)
    add_win.transient(root)
    add_win.grab_set()
    
    
    set_fullscreen(add_win)
    
    main_frame = create_samurai_frame(add_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=15)
    
    create_samurai_label(main_frame, "Создать новую категорию", 
                        font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=(0, 15))
    
    create_samurai_label(main_frame, "Название категории:", 
                        text_color=SAMURAI_TEXT).pack(anchor='w')
    name_entry = create_samurai_entry(main_frame, width=400)
    name_entry.pack(fill='x', pady=(5, 10))
    name_entry.focus()
    
    create_samurai_label(main_frame, "Описание (необязательно):", 
                        text_color=SAMURAI_TEXT).pack(anchor='w')
    desc_entry = create_samurai_textbox(main_frame, height=120)
    desc_entry.pack(fill='x', pady=(5, 15))
    
    def save_category():
        name = name_entry.get().strip()
        description = desc_entry.get("1.0", "end").strip()
        
        if not name:
            messagebox.showerror("Ошибка", "Введите название категории")
            return
        
        try:
            # ИЗМЕНЕНИЕ: Сохраняем информацию о том, кто создал категорию
            Category.create(
                name=name,
                description=description,
                created_by=current_user['username']  # Добавляем имя создателя
            )
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='add_category',
                target_username='System',
                details=f"Создана категория: {name} администратором {current_user['username']}"
            )
            
            messagebox.showinfo("Успех", f"Категория '{name}' создана")
            add_win.destroy()
            refresh_callback()  
            
        except Exception as e:
            if "Duplicate entry" in str(e):
                messagebox.showerror("Ошибка", "Категория с таким названием уже существует")
            else:
                logger.error(f"Ошибка создания категории: {e}")
                messagebox.showerror("Ошибка", f"Не удалось создать категорию: {str(e)}")
    
    button_frame = create_samurai_frame(main_frame, fg_color="transparent")
    button_frame.pack(fill='x')
    
    create_samurai_button(
        button_frame, 
        "💾 Сохранить", 
        save_category,
        color=SAMURAI_GREEN,
        hover_color=SAMURAI_GREEN_HOVER,
        width=130,
        height=35
    ).pack(side='left', padx=5)
    
    create_samurai_button(
        button_frame, 
        "✖ Отмена", 
        add_win.destroy,
        color=SAMURAI_RED,
        hover_color=SAMURAI_RED_HOVER,
        width=130,
        height=35
    ).pack(side='right', padx=5)


def edit_category_window(category, refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может редактировать категории")
        return
    
    edit_win = ctk.CTkToplevel(root)
    edit_win.title("Редактировать категорию")
    edit_win.geometry("500x400")
    edit_win.resizable(False, False)
    edit_win.configure(fg_color=SAMURAI_BG)
    edit_win.transient(root)
    edit_win.grab_set()
    
    
    set_fullscreen(edit_win)
    
    main_frame = create_samurai_frame(edit_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=15)
    
    create_samurai_label(main_frame, "Редактировать категорию", 
                        font=FONT_HEADER, text_color=SAMURAI_GOLD).pack(pady=(0, 15))
    
    create_samurai_label(main_frame, "Название категории:", 
                        text_color=SAMURAI_TEXT).pack(anchor='w')
    name_entry = create_samurai_entry(main_frame, width=400)
    name_entry.pack(fill='x', pady=(5, 10))
    name_entry.insert(0, category.name)
    name_entry.focus()
    
    create_samurai_label(main_frame, "Описание:", 
                        text_color=SAMURAI_TEXT).pack(anchor='w')
    desc_entry = create_samurai_textbox(main_frame, height=120)
    desc_entry.pack(fill='x', pady=(5, 15))
    if category.description:
        desc_entry.insert("1.0", category.description)
    
    def update_category():
        name = name_entry.get().strip()
        description = desc_entry.get("1.0", "end").strip()
        
        if not name:
            messagebox.showerror("Ошибка", "Введите название категории")
            return
        
        try:
            category.name = name
            category.description = description
            category.save()
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='edit_category',
                target_username='System',
                details=f"Изменена категория: {name} администратором {current_user['username']}"
            )
            
            messagebox.showinfo("Успех", "Категория обновлена")
            edit_win.destroy()
            refresh_callback()
            
        except Exception as e:
            if "Duplicate entry" in str(e):
                messagebox.showerror("Ошибка", "Категория с таким названием уже существует")
            else:
                logger.error(f"Ошибка обновления категории: {e}")
                messagebox.showerror("Ошибка", f"Не удалось обновить категорию: {str(e)}")
    
    button_frame = create_samurai_frame(main_frame, fg_color="transparent")
    button_frame.pack(fill='x')
    
    create_samurai_button(
        button_frame, 
        "💾 Сохранить", 
        update_category,
        color=SAMURAI_GREEN,
        hover_color=SAMURAI_GREEN_HOVER,
        width=130,
        height=35
    ).pack(side='left', padx=5)
    
    create_samurai_button(
        button_frame, 
        "✖ Отмена", 
        edit_win.destroy,
        color=SAMURAI_RED,
        hover_color=SAMURAI_RED_HOVER,
        width=130,
        height=35
    ).pack(side='right', padx=5)


def show_category_quotes_window(category):
    if not check_auth():
        return
    
    cat_win = ctk.CTkToplevel(root)
    cat_win.title(f"Категория: {category.name}")
    cat_win.geometry("900x600")
    cat_win.configure(fg_color=SAMURAI_BG)
    cat_win.transient(root)
    cat_win.grab_set()
    
    
    set_fullscreen(cat_win)
    
    main_frame = create_samurai_frame(cat_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, f"📁 {category.name}", 
                        font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=10)
    
    if category.description:
        create_samurai_label(main_frame, category.description, 
                           text_color=SAMURAI_TEXT_SECONDARY).pack(pady=5)
    
    
    table_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    table_frame.pack(fill='both', expand=True, pady=20)
    
    
    tree_frame = create_samurai_frame(table_frame, fg_color=SAMURAI_BG)
    tree_frame.pack(fill='both', expand=True)
    
    
    style = ttk.Style()
    style.configure("Category.Treeview", 
                    background=SAMURAI_CARD,
                    fieldbackground=SAMURAI_CARD,
                    foreground=SAMURAI_TEXT,
                    rowheight=60)
    style.configure("Category.Treeview.Heading",
                    background=SAMURAI_RED,
                    foreground="white")
    
    
    columns = ("type", "text", "author", "added_by")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                       style="Category.Treeview", height=20)
    
    tree.heading("type", text="Тип")
    tree.heading("text", text="Цитата")
    tree.heading("author", text="Автор")
    tree.heading("added_by", text="Добавил")
    
    tree.column("type", width=120, anchor="w", stretch=True)
    tree.column("text", width=500, anchor="w", stretch=True)
    tree.column("author", width=150, anchor="w", stretch=True)
    tree.column("added_by", width=120, anchor="w", stretch=True)
    
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    setup_touchpad_scrolling(tree)
    
    
    try:
        relations = CategoryQuote.select().where(
            CategoryQuote.category == category.id
        )
        
        type_labels = {
            'motivation': 'Мотивация',
            'affirmation': 'Аффирмация',
            'funny': 'Юмор'
        }
        
        for rel in relations:
            
            display_text = rel.quote_text
            if len(display_text) > 100:
                display_text = display_text[:100] + "..."
            
            
            added_by = rel.added_by if hasattr(rel, 'added_by') and rel.added_by else "Неизвестно"
            
            tree.insert("", "end", values=(
                type_labels.get(rel.quote_type, rel.quote_type),
                display_text,
                rel.quote_author,
                added_by  # Добавляем информацию о том, кто добавил цитату
            ))
        
        if not tree.get_children():
            create_samurai_label(
                table_frame,
                "В этой категории пока нет цитат",
                text_color=SAMURAI_TEXT_SECONDARY
            ).pack(pady=50)
            
    except Exception as e:
        logger.error(f"Ошибка загрузки цитат категории: {e}")
        create_samurai_label(
            table_frame,
            f"Ошибка загрузки: {str(e)}",
            text_color=SAMURAI_RED
        ).pack(pady=50)
    
    
    create_samurai_button(main_frame, "Закрыть", cat_win.destroy).pack(pady=10)


def manage_category_quotes_window(category, refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может управлять цитатами в категориях")
        return
    
    manage_win = ctk.CTkToplevel(root)
    manage_win.title(f"Управление цитатами в категории: {category.name}")
    manage_win.geometry("1400x800")
    manage_win.configure(fg_color=SAMURAI_BG)
    manage_win.transient(root)
    manage_win.grab_set()
    
    
    set_fullscreen(manage_win)
    
    main_frame = create_samurai_frame(manage_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    
    header_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_PANEL)
    header_frame.pack(fill='x', pady=10)
    
    create_samurai_label(
        header_frame, 
        f"Категория: {category.name}",
        font=FONT_TITLE,
        text_color=SAMURAI_GOLD
    ).pack(pady=10)
    
    if category.description:
        create_samurai_label(
            header_frame,
            category.description,
            text_color=SAMURAI_TEXT_SECONDARY
        ).pack(pady=(0, 10))
    
    
    manual_btn_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_BG)
    manual_btn_frame.pack(fill='x', pady=10)
    
    create_samurai_button(
        manual_btn_frame,
        "✏️ Добавить цитату вручную",
        lambda: add_manual_quote_to_category(category, lambda: load_category_quotes_tab_content(quotes_in_cat_tab, category, refresh_callback)),
        color=SAMURAI_GREEN,
        hover_color=SAMURAI_GREEN_HOVER,
        width=200
    ).pack(side='left', padx=5)
    
    
    tabview = ctk.CTkTabview(
        main_frame,
        fg_color=SAMURAI_PANEL,
        segmented_button_fg_color=SAMURAI_BG,
        segmented_button_selected_color=SAMURAI_RED,
        segmented_button_selected_hover_color=SAMURAI_RED_HOVER
    )
    tabview.pack(fill='both', expand=True, pady=10)
    
    tabview.add("Цитаты в категории")
    tabview.add("Добавить из существующих")
    
    
    quotes_in_cat_tab = tabview.tab("Цитаты в категории")
    
    def load_category_quotes_tab_content(parent_tab, cat, refresh):
        for widget in parent_tab.winfo_children():
            widget.destroy()
        
        
        controls_frame = create_samurai_frame(parent_tab, fg_color=SAMURAI_BG)
        controls_frame.pack(fill='x', pady=10)
        
        
        search_frame = create_samurai_frame(controls_frame, fg_color="transparent")
        search_frame.pack(fill='x', pady=5)
        
        create_samurai_label(search_frame, "Поиск:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
        search_entry = create_samurai_entry(search_frame, width=300)
        search_entry.pack(side='left', padx=5)
        
        def search_quotes():
            load_quotes(search_entry.get().strip())
        
        create_samurai_button(
            search_frame,
            "🔍 Найти",
            search_quotes,
            width=80
        ).pack(side='left', padx=5)
        
        
        sort_frame = create_samurai_frame(controls_frame, fg_color="transparent")
        sort_frame.pack(fill='x', pady=5)
        
        create_samurai_label(sort_frame, "Сортировка:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
        
        sort_var = ctk.StringVar(value="default")
        
        def sort_quotes():
            load_quotes(search_entry.get().strip(), sort_var.get())
        
        ctk.CTkRadioButton(
            sort_frame,
            text="По умолчанию",
            variable=sort_var,
            value="default",
            command=sort_quotes,
            fg_color=SAMURAI_RED,
            text_color=SAMURAI_TEXT
        ).pack(side='left', padx=10)
        
        ctk.CTkRadioButton(
            sort_frame,
            text="А→Я",
            variable=sort_var,
            value="asc",
            command=sort_quotes,
            fg_color=SAMURAI_RED,
            text_color=SAMURAI_TEXT
        ).pack(side='left', padx=10)
        
        ctk.CTkRadioButton(
            sort_frame,
            text="Я→А",
            variable=sort_var,
            value="desc",
            command=sort_quotes,
            fg_color=SAMURAI_RED,
            text_color=SAMURAI_TEXT
        ).pack(side='left', padx=10)
        
        
        filter_frame = create_samurai_frame(controls_frame, fg_color="transparent")
        filter_frame.pack(fill='x', pady=5)
        
        create_samurai_label(filter_frame, "Фильтр по автору:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
        
        
        authors = CategoryQuote.select(CategoryQuote.quote_author).where(
            CategoryQuote.category == cat.id
        ).distinct()
        
        author_list = ["Все"] + [a.quote_author for a in authors if a.quote_author]
        author_var = ctk.StringVar(value="Все")
        
        author_combo = ctk.CTkComboBox(
            filter_frame,
            values=author_list,
            variable=author_var,
            fg_color=SAMURAI_PANEL,
            border_color=SAMURAI_GOLD,
            button_color=SAMURAI_RED,
            button_hover_color=SAMURAI_RED_HOVER,
            dropdown_fg_color=SAMURAI_PANEL,
            dropdown_hover_color=SAMURAI_RED,
            dropdown_text_color="white",
            width=200,
            command=lambda x: load_quotes(search_entry.get().strip(), sort_var.get())
        )
        author_combo.pack(side='left', padx=5)
        
        
        create_samurai_button(
            filter_frame,
            "🔄 Сбросить",
            lambda: [search_entry.delete(0, 'end'), 
                    sort_var.set("default"),
                    author_var.set("Все"),
                    load_quotes()],
            width=80
        ).pack(side='left', padx=5)
        
        
        create_samurai_button(
            controls_frame,
            "🗑️ Удалить все цитаты",
            lambda: remove_all_from_category(cat, refresh, lambda: load_quotes()),
            color=SAMURAI_RED,
            hover_color=SAMURAI_RED_HOVER,
            width=150
        ).pack(side='right', padx=5)
        
        
        table_frame = create_samurai_frame(parent_tab, fg_color=SAMURAI_BG)
        table_frame.pack(fill='both', expand=True)
        
        
        tree_frame = create_samurai_frame(table_frame, fg_color=SAMURAI_BG)
        tree_frame.pack(fill='both', expand=True)
        
        
        columns = ("type", "text", "author", "added_by", "added")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20, selectmode='extended')
        
        tree.heading("type", text="Тип")
        tree.heading("text", text="Цитата")
        tree.heading("author", text="Автор")
        tree.heading("added_by", text="Добавил")
        tree.heading("added", text="Дата добавления")
        
        tree.column("type", width=100, anchor="w")
        tree.column("text", width=600, anchor="w")
        tree.column("author", width=200, anchor="w")
        tree.column("added_by", width=120, anchor="w")
        tree.column("added", width=150, anchor="w")
        
        
        for col in columns:
            tree.column(col, stretch=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        setup_touchpad_scrolling(tree)
        
        
        context_menu = Menu(root, tearoff=0, bg=SAMURAI_PANEL, fg="white")
        context_menu.add_command(label="🗑️ Удалить выбранные из категории", 
                                command=lambda: remove_selected_from_category(tree, cat, refresh))
        context_menu.add_separator()
        context_menu.add_command(label="❌ Отмена")
        
        def show_context_menu(event):
            item = tree.identify_row(event.y)
            if item:
                tree.selection_set(item)
                context_menu.post(event.x_root, event.y_root)
        
        tree.bind("<Button-3>", show_context_menu)
        tree.bind("<Delete>", lambda e: remove_selected_from_category(tree, cat, refresh))
        
        def load_quotes(search_text="", sort_order="default"):
            for item in tree.get_children():
                tree.delete(item)
            
            try:
                
                query = CategoryQuote.select().where(
                    CategoryQuote.category == cat.id
                )
                
                
                if search_text:
                    query = query.where(CategoryQuote.quote_text.contains(search_text))
                
                
                if author_var.get() != "Все":
                    query = query.where(CategoryQuote.quote_author == author_var.get())
                
                
                if sort_order == "asc":
                    query = query.order_by(CategoryQuote.quote_text.asc())
                elif sort_order == "desc":
                    query = query.order_by(CategoryQuote.quote_text.desc())
                else:
                    query = query.order_by(CategoryQuote.added_at.desc())
                
                type_labels = {
                    'motivation': 'Мотивация',
                    'affirmation': 'Аффирмация',
                    'funny': 'Юмор'
                }
                
                for rel in query:
                    
                    display_text = rel.quote_text
                    if len(display_text) > 80:
                        display_text = display_text[:80] + "..."
                    
                    added_date = rel.added_at.strftime('%d.%m.%Y') if rel.added_at else "—"
                    
                    # ИЗМЕНЕНИЕ: Показываем имя пользователя, который добавил цитату
                    added_by = rel.added_by if hasattr(rel, 'added_by') and rel.added_by else "Неизвестно"
                    
                    tree.insert("", "end", values=(
                        type_labels.get(rel.quote_type, rel.quote_type),
                        display_text,
                        rel.quote_author,
                        added_by,  # Добавляем информацию о том, кто добавил цитату
                        added_date
                    ), tags=(rel.id,))
            
            except Exception as e:
                logger.error(f"Ошибка загрузки цитат категории: {e}")
        
        
        search_entry.bind("<Return>", lambda e: search_quotes())
        
        
        load_quotes()
    
    
    load_category_quotes_tab_content(quotes_in_cat_tab, category, refresh_callback)
    
    
    add_quotes_tab = tabview.tab("Добавить из существующих")
    load_add_quotes_tab(add_quotes_tab, category, refresh_callback)


def load_add_quotes_tab(parent, category, refresh_callback):
    
    
    def get_model_by_type(type_str):
        if type_str == "Мотивация":
            return Motivation
        elif type_str == "Аффирмации":
            return Affirmation
        else:  
            return FunnyQuote
    
    
    filter_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    filter_frame.pack(fill='x', pady=10)
    
    create_samurai_label(filter_frame, "Тип цитат:", 
                        text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    quote_type_var = ctk.StringVar(value="Мотивация")
    
    type_combobox = ctk.CTkComboBox(
        filter_frame,
        values=["Мотивация", "Аффирмации", "Юмор"],
        variable=quote_type_var,
        fg_color=SAMURAI_PANEL,
        border_color=SAMURAI_GOLD,
        button_color=SAMURAI_RED,
        button_hover_color=SAMURAI_RED_HOVER,
        dropdown_fg_color=SAMURAI_PANEL,
        dropdown_hover_color=SAMURAI_RED,
        dropdown_text_color="white",
        width=150
    )
    type_combobox.pack(side='left', padx=5)
    

    search_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    search_frame.pack(fill='x', pady=10)
    
    create_samurai_label(search_frame, "Поиск:", 
                        text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    search_entry = create_samurai_entry(search_frame, width=300)
    search_entry.pack(side='left', padx=5)
    
    def search_quotes():
        load_quotes_list(search_entry.get().strip())
    
    create_samurai_button(
        search_frame,
        "🔍 Найти",
        search_quotes,
        width=80
    ).pack(side='left', padx=5)
    
    create_samurai_button(
        search_frame,
        "🔄 Показать все",
        lambda: load_quotes_list(),
        width=100
    ).pack(side='left', padx=5)
    
    author_filter_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    author_filter_frame.pack(fill='x', pady=5)
    
    create_samurai_label(author_filter_frame, "Фильтр по автору:", 
                        text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    author_var = ctk.StringVar(value="Все")
    author_combo = ctk.CTkComboBox(
        author_filter_frame,
        values=["Все"],
        variable=author_var,
        fg_color=SAMURAI_PANEL,
        border_color=SAMURAI_GOLD,
        button_color=SAMURAI_RED,
        button_hover_color=SAMURAI_RED_HOVER,
        width=200,
        command=lambda x: load_quotes_list(search_entry.get().strip())
    )
    author_combo.pack(side='left', padx=5)
    
    sort_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    sort_frame.pack(fill='x', pady=5)
    
    create_samurai_label(sort_frame, "Сортировка:", text_color=SAMURAI_TEXT).pack(side='left', padx=5)
    
    sort_var = ctk.StringVar(value="default")
    
    def sort_quotes():
        load_quotes_list(search_entry.get().strip())
    
    ctk.CTkRadioButton(
        sort_frame,
        text="По умолчанию",
        variable=sort_var,
        value="default",
        command=sort_quotes,
        fg_color=SAMURAI_RED,
        text_color=SAMURAI_TEXT
    ).pack(side='left', padx=10)
    
    ctk.CTkRadioButton(
        sort_frame,
        text="А→Я",
        variable=sort_var,
        value="asc",
        command=sort_quotes,
        fg_color=SAMURAI_RED,
        text_color=SAMURAI_TEXT
    ).pack(side='left', padx=10)
    
    ctk.CTkRadioButton(
        sort_frame,
        text="Я→А",
        variable=sort_var,
        value="desc",
        command=sort_quotes,
        fg_color=SAMURAI_RED,
        text_color=SAMURAI_TEXT
    ).pack(side='left', padx=10)
    
    
    table_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    table_frame.pack(fill='both', expand=True, pady=10)
    
    columns = ("id", "text", "author", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20, selectmode='extended')
    
    tree.heading("id", text="ID")
    tree.heading("text", text="Цитата")
    tree.heading("author", text="Автор")
    tree.heading("status", text="Статус")
    
    tree.column("id", width=50, anchor="w")
    tree.column("text", width=600, anchor="w")
    tree.column("author", width=200, anchor="w")
    tree.column("status", width=100, anchor="w")
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    setup_touchpad_scrolling(tree)
    
    context_menu = Menu(root, tearoff=0, bg=SAMURAI_PANEL, fg="white")
    context_menu.add_command(label="➕ Добавить выбранные в категорию", 
                            command=lambda: add_selected_to_category(tree, category, quote_type_var.get(), refresh_callback))
    context_menu.add_separator()
    context_menu.add_command(label="❌ Отмена")
    
    def show_context_menu(event):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            context_menu.post(event.x_root, event.y_root)
    
    tree.bind("<Button-3>", show_context_menu)
    
    def on_double_click(event):
        selection = tree.selection()
        if selection:
            add_selected_to_category(tree, category, quote_type_var.get(), refresh_callback)
    
    tree.bind("<Double-1>", on_double_click)
    
    btn_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    btn_frame.pack(fill='x', pady=10)
    
    create_samurai_button(
        btn_frame,
        "➕ Добавить выбранные в категорию",
        lambda: add_selected_to_category(tree, category, quote_type_var.get(), refresh_callback),
        color=SAMURAI_GREEN,
        hover_color=SAMURAI_GREEN_HOVER,
        width=250
    ).pack()
    
    hint_label = create_samurai_label(
        btn_frame,
        "💡 Подсказка: используйте Ctrl+клик для множественного выбора, Shift для диапазона",
        text_color=SAMURAI_TEXT_SECONDARY,
        font=('Segoe UI', 9, 'italic')
    )
    hint_label.pack(pady=5)
    
    def load_quotes_list(search_text=""):
        for item in tree.get_children():
            tree.delete(item)
        
        try:
            model = get_model_by_type(quote_type_var.get())
            type_key = quote_type_var.get().lower()
            if type_key == "аффирмации":
                type_key = "affirmation"
            elif type_key == "мотивация":
                type_key = "motivation"
            elif type_key == "юмор":
                type_key = "funny"
            
            
            added_quotes = CategoryQuote.select().where(
                CategoryQuote.category == category.id
            )
            added_texts = [q.quote_text for q in added_quotes]
            
            
            query = model.select().where(model.is_deleted == False)
            
            
            if search_text:
                query = query.where(model.text.contains(search_text))
            
            
            quotes_list = list(query)
            
            
            if quotes_list:
                
                authors = set(q.author for q in quotes_list if q.author)
                author_combo.configure(values=["Все"] + sorted(list(authors)))
            
            
            filtered_quotes = [q for q in quotes_list if q.text not in added_texts]
            
            
            if sort_var.get() == "asc":
                filtered_quotes.sort(key=lambda x: x.text)
            elif sort_var.get() == "desc":
                filtered_quotes.sort(key=lambda x: x.text, reverse=True)
            
            for quote in filtered_quotes:
                display_text = quote.text
                if len(display_text) > 80:
                    display_text = display_text[:80] + "..."
                
                tree.insert("", "end", values=(
                    quote.id,
                    display_text,
                    quote.author if quote.author else "—",
                    "Активна"
                ))
            
            
            if not filtered_quotes:
                tree.insert("", "end", values=(
                    "",
                    "Нет доступных цитат для добавления",
                    "",
                    ""
                ))
        
        except Exception as e:
            logger.error(f"Ошибка загрузки списка цитат: {e}")
            tree.insert("", "end", values=(
                "",
                f"Ошибка загрузки: {str(e)}",
                "",
                ""
            ))
    
    
    def on_type_change(*args):
        load_quotes_list()
    
    quote_type_var.trace_add("write", on_type_change)
    search_entry.bind("<Return>", lambda e: search_quotes())
    author_var.trace_add("write", lambda *args: load_quotes_list(search_entry.get().strip()))
    
    
    load_quotes_list()


def add_selected_to_category(tree, category, type_str, refresh_callback):
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Выбор", "Выберите цитаты для добавления")
        return
    
    
    def get_model_by_type(type_str):
        if type_str == "Мотивация":
            return Motivation
        elif type_str == "Аффирмации":
            return Affirmation
        else:
            return FunnyQuote
    
    model = get_model_by_type(type_str)
    type_key = type_str.lower()
    if type_key == "аффирмации":
        type_key = "affirmation"
    elif type_key == "мотивация":
        type_key = "motivation"
    elif type_key == "юмор":
        type_key = "funny"
    
    added_count = 0
    skipped_count = 0
    errors = []
    
    for item in selection:
        values = tree.item(item, "values")
        try:
            quote_id = int(values[0])
        except (ValueError, IndexError):
            skipped_count += 1
            continue
        
        try:
            
            quote = model.get_by_id(quote_id)
            
            
            try:
                CategoryQuote.get(
                    (CategoryQuote.category == category.id) &
                    (CategoryQuote.quote_text == quote.text)
                )
                skipped_count += 1
                continue  
            except CategoryQuote.DoesNotExist:
                pass
            
            
            
            CategoryQuote.create(
                category=category.id,
                quote_type=type_key,
                quote_text=quote.text,
                quote_author=quote.author if quote.author else "Неизвестный",
                added_by=current_user['username']  
            )
            added_count += 1
            
            
            tree.delete(item)
            
        except Exception as e:
            logger.error(f"Ошибка добавления цитаты {quote_id}: {e}")
            errors.append(str(e))
    
    if added_count > 0:
        AdminActionLog.create(
            admin_username=current_user['username'],
            action_type='add_quotes_to_category',
            target_username='System',
            details=f"Добавлено {added_count} цитат в категорию {category.name} администратором {current_user['username']}"
        )
        
        message = f"✅ Добавлено: {added_count} цитат\n"
        if skipped_count > 0:
            message += f"⏭️ Пропущено (уже есть): {skipped_count}\n"
        if errors:
            message += f"❌ Ошибок: {len(errors)}"
        
        messagebox.showinfo("Результат", message)
        
        refresh_callback()  
    else:
        messagebox.showinfo("Информация", "Ни одна из выбранных цитат не была добавлена")


def remove_selected_from_category(tree, category, refresh_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может удалять цитаты из категорий")
        return
    
    selection = tree.selection()
    if not selection:
        messagebox.showwarning("Выбор", "Выберите цитаты для удаления")
        return
    
    quote_texts = []
    for item in selection:
        values = tree.item(item, "values")
        if len(values) > 1:
            quote_texts.append(values[1])
    
    if messagebox.askyesno("Подтверждение", 
                          f"Убрать выбранные цитаты из категории?\n\n"
                          f"Выбрано: {len(selection)} цитат\n\n"
                          f"Это действие нельзя отменить."):
        removed_count = 0
        for item in selection:
            try:
                rel_id = tree.item(item, "tags")[0]
                CategoryQuote.delete().where(CategoryQuote.id == rel_id).execute()
                tree.delete(item)
                removed_count += 1
            except Exception as e:
                logger.error(f"Ошибка удаления из категории: {e}")
        
        if removed_count > 0:
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='remove_quotes_from_category',
                target_username='System',
                details=f"Удалено {removed_count} цитат из категории {category.name} администратором {current_user['username']}"
            )
            
            messagebox.showinfo("Успех", f"Удалено {removed_count} цитат из категории")
            refresh_callback()


def remove_all_from_category(category, refresh_callback, load_quotes_callback):
    if current_user['role'] != 'администратор':
        messagebox.showerror("Ошибка", "Только Сёгун может удалять цитаты из категорий")
        return
    
    
    quotes_count = CategoryQuote.select().where(CategoryQuote.category == category.id).count()
    
    if quotes_count == 0:
        messagebox.showinfo("Информация", "В категории нет цитат")
        return
    
    if messagebox.askyesno("Подтверждение", 
                          f"Вы уверены, что хотите удалить ВСЕ цитаты из категории '{category.name}'?\n\n"
                          f"Количество цитат: {quotes_count}\n\n"
                          f"Это действие нельзя отменить."):
        try:
            
            deleted = CategoryQuote.delete().where(CategoryQuote.category == category.id).execute()
            
            
            AdminActionLog.create(
                admin_username=current_user['username'],
                action_type='remove_all_quotes_from_category',
                target_username='System',
                details=f"Удалено {deleted} цитат из категории {category.name} администратором {current_user['username']}"
            )
            
            messagebox.showinfo("Успех", f"Удалено {deleted} цитат из категории")
            load_quotes_callback() 
            refresh_callback()  
            
        except Exception as e:
            logger.error(f"Ошибка удаления всех цитат из категории: {e}")
            messagebox.showerror("Ошибка", f"Не удалось удалить цитаты: {str(e)}")


def show_tooltip(event, text):
    try:
        tooltip = tk.Toplevel(root)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, justify='left',
                        background=SAMURAI_PANEL, foreground="white",
                        relief='solid', borderwidth=1, font=("Segoe UI", 9))
        label.pack()
        
        
        event.widget.tooltip = tooltip
    except:
        pass

def hide_tooltip(event):
    if hasattr(event.widget, 'tooltip'):
        try:
            event.widget.tooltip.destroy()
        except:
            pass
        delattr(event.widget, 'tooltip')


def developer_window():
    if not check_auth():
        return
    
   
    if not is_main_admin():
        messagebox.showerror("Ошибка", "Только главный Сёгун имеет доступ к панели управления")
        return
    
    dev_win = ctk.CTkToplevel(root)
    dev_win.title("Сёгун - Панель управления")
    dev_win.geometry("900x600")
    dev_win.configure(fg_color=SAMURAI_BG)
    dev_win.transient(root)
    dev_win.grab_set()
    
    
    set_fullscreen(dev_win)
    
    main_frame = create_samurai_frame(dev_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, "Панель Сёгуна", font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=10)
    
    
    content_frame = create_samurai_frame(main_frame, fg_color=SAMURAI_PANEL)
    content_frame.pack(fill='x', padx=20, pady=10)
    
    
    button_row = create_samurai_frame(content_frame, fg_color="transparent")
    button_row.pack(pady=10)
    
    create_samurai_button(
        button_row, 
        "📜 Управление свитками (БД)", 
        manage_quotes_window,
        width=200
    ).pack(side='left', padx=5)
    
    
    tabview = ctk.CTkTabview(
        main_frame,
        fg_color=SAMURAI_PANEL,
        segmented_button_fg_color=SAMURAI_BG,
        segmented_button_selected_color=SAMURAI_RED,
        segmented_button_selected_hover_color=SAMURAI_RED_HOVER,
        text_color=SAMURAI_TEXT
    )
    tabview.pack(fill='both', expand=True, padx=20, pady=10)
    
    tabview.add("Заявки")
    load_requests_tab(tabview.tab("Заявки"))
    
    create_samurai_button(main_frame, "Закрыть", dev_win.destroy).pack(pady=10)


def load_requests_tab(parent):
    status_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    status_frame.pack(fill='x', pady=5)
    
    create_samurai_label(status_frame, "Статус: Главный Сёгун", 
                       text_color=SAMURAI_GREEN, font=FONT_BOLD).pack(side='left')
    
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
    
    
    set_fullscreen(manage_win)
    
    main_frame = create_samurai_frame(manage_win, fg_color=SAMURAI_BG)
    main_frame.pack(fill='both', expand=True, padx=20, pady=20)
    
    create_samurai_label(main_frame, "Управление свитками мудрости", 
                       font=FONT_TITLE, text_color=SAMURAI_GOLD).pack(pady=10)
    
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
    
    load_quotes_tab(tabview.tab("Мотивация"), Motivation, 'motivation')
    load_quotes_tab(tabview.tab("Аффирмации"), Affirmation, 'affirmation')
    load_quotes_tab(tabview.tab("Юмор"), FunnyQuote, 'funny')
    
    create_samurai_label(main_frame, "* Все изменения сохраняются в свитки знаний", 
                       text_color=SAMURAI_TEXT_SECONDARY, font=('Segoe UI', 10)).pack(pady=5)
    
    create_samurai_button(main_frame, "Закрыть", manage_win.destroy).pack(pady=10)


def load_quotes_tab(parent, ModelClass, quote_type):
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
    
    table_frame = create_samurai_frame(parent, fg_color=SAMURAI_BG)
    table_frame.pack(fill='both', expand=True)
    
    columns = ("text", "author", "status")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)
    
    tree.heading("text", text="Мудрость")
    tree.heading("author", text="Автор")
    tree.heading("status", text="Статус")
    
    tree.column("text", width=600, anchor="w", stretch=True)
    tree.column("author", width=200, anchor="w", stretch=True)
    tree.column("status", width=100, anchor="w", stretch=True)
    
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    setup_touchpad_scrolling(tree)

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
    
    
    set_fullscreen(add_win)
    
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
        
        if not author:
            if quote_type == 'affirmation':
                author = ""
            else:
                author = "Неизвестный"
        
        try:
            models = {
                'motivation': Motivation,
                'affirmation': Affirmation,
                'funny': FunnyQuote
            }
            model = models[quote_type]
            model.create(text=text, author=author)
            
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
        
        
        set_fullscreen(edit_win)
        
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
            
            if not author:
                if quote_type == 'affirmation':
                    author = ""
                else:
                    author = "Неизвестный"
            
            try:
                quote.text = text
                quote.author = author
                quote.save()
                
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
        
        
        set_fullscreen(del_win)
        
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


if __name__ == "__main__":
    init_db()
    show_auth_window()
    root.mainloop()