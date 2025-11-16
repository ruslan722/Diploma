import tkinter as tk
from tkinter import Label, Frame, Canvas, PhotoImage
import webbrowser
from PIL import Image, ImageTk

root = tk.Tk()
root.title('Информационная система мотивационных высказываний')
root.geometry('1280x800')
root.configure(bg='white')
root.resizable(True, True)

# ---------- Верхнее меню ----------
menu_root = Frame(root, bg='#7773C1', height=100)
menu_root.pack(fill='x', side='top')

icon_image = PhotoImage(file='content/icon.png')
icon_img_small = icon_image.subsample(15)
Label(menu_root, image=icon_img_small, bg='#7773C1').pack(side='left', padx=20, pady=10)

menu_items_frame = Frame(menu_root, bg='#7773C1')
menu_items_frame.pack(side='left', padx=50, pady=10)

Label(menu_items_frame, text='Главная', bg="#7773C1", fg='black', font=('Arial', 16, 'bold')).grid(row=0, column=0, padx=20)
Label(menu_items_frame, text='Мотивация', bg='#7773C1', fg='black', font=('Arial', 16)).grid(row=0, column=1, padx=20)
Label(menu_items_frame, text='Аффирмация', bg='#7773C1', fg='black', font=('Arial', 16)).grid(row=0, column=2, padx=20)
Label(menu_items_frame, text='Смешные цитаты', bg='#7773C1', fg='black', font=('Arial', 16)).grid(row=0, column=3, padx=20)

auth_frame = Frame(menu_root, bg='#7773C1')
auth_frame.pack(side='right', padx=20, pady=10)
Label(auth_frame, text='Войти', bg='#7773C1', fg='black', font=('Arial', 16, 'bold'),
      width=8, height=1).grid(row=0, column=0, padx=10)
Label(auth_frame, text='Регистрация', bg='#7773C1', fg='black', font=('Arial', 16, 'bold'),
      width=12, height=1).grid(row=0, column=1, padx=10)

# ---------- Прокручиваемая область ----------
home_window = Frame(root, bg='white')
home_window.pack(fill='both', expand=True)

canvas = Canvas(home_window, bg='white', highlightthickness=0)
canvas.pack(side='left', fill='both', expand=True)

scrollbar = tk.Scrollbar(home_window, orient='vertical', command=canvas.yview)
scrollbar.pack(side='right', fill='y')

canvas.configure(yscrollcommand=scrollbar.set)

scrollable_frame = Frame(canvas, bg='white')
window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

def on_canvas_configure(event):
    canvas.itemconfig(window_id, width=event.width)

canvas.bind('<Configure>', on_canvas_configure)

def update_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", update_scrollregion)

scrollable_frame.grid_columnconfigure(0, weight=1)

# ---------- Центральный контейнер ----------
center_container = Frame(scrollable_frame, bg='white')
center_container.grid(row=0, column=0, sticky='ew', pady=10)
center_container.grid_columnconfigure(0, weight=1)

# ---------- Контент ----------
img = PhotoImage(file='content/1.png')
main_img = img.subsample(2)
root._main_img = main_img

img_label = Label(center_container, image=main_img, bg='white')
img_label.grid(row=0, column=0, pady=(10, 20))

blue_frame = Frame(center_container, bg="#444258")
blue_frame.grid(row=1, column=0, pady=(0, 20))

info_label = Label(blue_frame, text='Добро пожаловать', bg='#080627', fg='white',
                   font=('Arial', 24, 'bold'))
info_label.pack(pady=(20, 10), padx=60)

developer_info = Label(
    blue_frame,
    text='Разработчик: Оноприенко Р. А. \n\n'
         'Телефон: +79632181240\n'
         'Email: raleksandrovic619@gmail.com',
    bg="#080627", fg='white',
    font=('Arial', 18), justify='center'
)
developer_info.pack(pady=(0, 20), padx=60)

# ---------- Социальные сети ----------
social_frame = Frame(center_container, bg='white')
social_frame.grid(row=2, column=0, pady=20, sticky='ew')
social_frame.grid_columnconfigure(0, weight=1)

social_container = Frame(social_frame, bg='white')
social_container.grid(row=0, column=0, sticky='e', padx=100)

def open_link(url):
    webbrowser.open_new(url)

# ---------- Функция загрузки пары изображений (обычное + увеличенное) ----------
def load_icon(path):
    img = Image.open(path)
    w, h = img.size

    normal = ImageTk.PhotoImage(img.resize((int(w * 0.12), int(h * 0.12))))
    big     = ImageTk.PhotoImage(img.resize((int(w * 0.16), int(h * 0.16))))

    return normal, big

tg_normal, tg_big = load_icon("content/tg.png")
x_normal, x_big   = load_icon("content/x.png")
vk_normal, vk_big = load_icon("content/vk.png")

root._icons = (tg_normal, tg_big, x_normal, x_big, vk_normal, vk_big)

# ---------- Анимация наведения ----------
def apply_hover(widget, normal_img, big_img):
    widget.bind("<Enter>", lambda e: widget.config(image=big_img))
    widget.bind("<Leave>", lambda e: widget.config(image=normal_img))

# ---------- Кнопки соцсетей ----------
tg_btn = Label(social_container, image=tg_normal, bg='white', cursor='hand2')
tg_btn.pack(side='left', padx=20)
tg_btn.bind("<Button-1>", lambda e: open_link("https://t.me/GoodFleck"))
apply_hover(tg_btn, tg_normal, tg_big)

x_btn = Label(social_container, image=x_normal, bg='white', cursor='hand2')
x_btn.pack(side='left', padx=20)
x_btn.bind("<Button-1>", lambda e: open_link("https://x.com/Wolv_18"))
apply_hover(x_btn, x_normal, x_big)

vk_btn = Label(social_container, image=vk_normal, bg='white', cursor='hand2')
vk_btn.pack(side='left', padx=20)
vk_btn.bind("<Button-1>", lambda e: open_link("https://vk.com/huwzan"))
apply_hover(vk_btn, vk_normal, vk_big)

# ---------- Прокрутка колесом ----------
def on_mouse_wheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", on_mouse_wheel)

root.mainloop()
