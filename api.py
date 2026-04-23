from fastapi import FastAPI, Request, Query, Response, File, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from typing import Optional
import re
from datetime import datetime
import random
import hashlib
import secrets
import json
import os
import shutil
from pathlib import Path

from connect import Motivation, Affirmation, FunnyQuote, Avtorization, \
    UserReaction, UserProfile, Category, CategoryQuote

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Директория для аватаров
AVATARS_DIR = Path("static/avatars")
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

# Секретный ключ для сессий
SECRET_KEY = "your-secret-key-here-change-in-production"
SESSION_COOKIE_NAME = "session_id"

# Хранилище сессий
sessions = {}

def create_session(username: str) -> str:
    """Создание новой сессии"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "username": username,
        "created_at": datetime.now()
    }
    return session_id

def get_session_user(request: Request) -> Optional[dict]:
    """Получение пользователя из сессии"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and session_id in sessions:
        return sessions[session_id]
    return None

def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user_context(request: Request) -> dict:
    """Получение контекста текущего пользователя для шаблонов"""
    session_user = get_session_user(request)
    if session_user:
        user_profile = UserProfile.get_or_none(UserProfile.username == session_user["username"])
        if user_profile:
            # Получаем статистику
            likes_count = UserReaction.select().where(
                (UserReaction.username == session_user["username"]) &
                (UserReaction.reaction == 'like')
            ).count()
            
            dislikes_count = UserReaction.select().where(
                (UserReaction.username == session_user["username"]) &
                (UserReaction.reaction == 'dislike')
            ).count()

            return {
                "is_authenticated": True,
                "username": user_profile.username,
                "nickname": user_profile.nickname or user_profile.username,
                "avatar_path": user_profile.avatar_path,
                "user_id": user_profile.id,
                "stats": {
                    "likes": likes_count,
                    "dislikes": dislikes_count,
                    "total": likes_count + dislikes_count
                }
            }
    return {"is_authenticated": False}

# Функция для безопасного выделения текста
def highlight_text(text, search_term):
    if not search_term or not text:
        return text
    pattern = re.compile(f'({re.escape(search_term)})', re.IGNORECASE)
    return pattern.sub(r'<span class="highlight">\1</span>', str(text))

# Функция для преобразования цитаты в JSON-сериализуемый словарь
def quote_to_dict(quote, quote_type):
    return {
        'id': quote.id,
        'text': quote.text,
        'author': quote.author if quote.author else ''
    }

# ========== ЭНДПОИНТЫ АВТОРИЗАЦИИ ==========

@app.post('/api/auth/register')
async def register(request: Request):
    """Регистрация нового пользователя"""
    try:
        data = await request.json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        nickname = data.get('nickname', '').strip()

        # Валидация
        if not username or not password:
            return JSONResponse(
                {"success": False, "message": "Имя пользователя и пароль обязательны"},
                status_code=400
            )

        if len(username) < 3:
            return JSONResponse(
                {"success": False, "message": "Имя пользователя должно быть не менее 3 символов"},
                status_code=400
            )

        if len(password) < 4:
            return JSONResponse(
                {"success": False, "message": "Пароль должен быть не менее 4 символов"},
                status_code=400
            )

        # Проверяем, существует ли пользователь в Avtorization
        existing_user = Avtorization.get_or_none(Avtorization.username == username)
        if existing_user:
            return JSONResponse(
                {"success": False, "message": "Пользователь с таким именем уже существует"},
                status_code=400
            )

        # Создаем пользователя
        hashed_password = hash_password(password)
        
        # Создаем запись в Avtorization
        auth_user = Avtorization.create(
            username=username,
            password=hashed_password
        )

        # Создаем профиль пользователя
        UserProfile.create(
            username=username,
            nickname=nickname or username,
            avatar_path=None
        )

        # Создаем сессию
        session_id = create_session(username)

        response = JSONResponse({
            "success": True,
            "message": "Регистрация успешна",
            "username": username
        })
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=30 * 24 * 60 * 60,
            samesite='lax'
        )
        return response

    except Exception as e:
        print(f"Error in register: {e}")
        return JSONResponse(
            {"success": False, "message": f"Ошибка при регистрации: {str(e)}"},
            status_code=500
        )


@app.post('/api/auth/login')
async def login(request: Request):
    """Вход пользователя"""
    try:
        data = await request.json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return JSONResponse(
                {"success": False, "message": "Имя пользователя и пароль обязательны"},
                status_code=400
            )

        # Проверяем пользователя
        user = Avtorization.get_or_none(Avtorization.username == username)
        if not user:
            return JSONResponse(
                {"success": False, "message": "Неверное имя пользователя или пароль"},
                status_code=401
            )

        hashed_password = hash_password(password)
        if user.password != hashed_password:
            return JSONResponse(
                {"success": False, "message": "Неверное имя пользователя или пароль"},
                status_code=401
            )

        # Создаем сессию
        session_id = create_session(username)
        
        # Устанавливаем cookie
        response = JSONResponse({
            "success": True,
            "message": "Вход выполнен успешно",
            "username": username
        })
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            httponly=True,
            max_age=30 * 24 * 60 * 60,
            samesite='lax'
        )

        return response

    except Exception as e:
        print(f"Error in login: {e}")
        return JSONResponse(
            {"success": False, "message": f"Ошибка при входе: {str(e)}"},
            status_code=500
        )


@app.post('/api/auth/logout')
async def logout(request: Request):
    """Выход пользователя"""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and session_id in sessions:
        del sessions[session_id]

    response = JSONResponse({"success": True, "message": "Выход выполнен"})
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@app.get('/api/auth/me')
async def get_current_user_api(request: Request):
    """Получение информации о текущем пользователе"""
    session_user = get_session_user(request)
    if session_user:
        user_profile = UserProfile.get_or_none(UserProfile.username == session_user["username"])
        if user_profile:
            likes_count = UserReaction.select().where(
                (UserReaction.username == session_user["username"]) &
                (UserReaction.reaction == 'like')
            ).count()
            
            dislikes_count = UserReaction.select().where(
                (UserReaction.username == session_user["username"]) &
                (UserReaction.reaction == 'dislike')
            ).count()

            return JSONResponse({
                "is_authenticated": True,
                "username": user_profile.username,
                "nickname": user_profile.nickname or user_profile.username,
                "avatar_path": user_profile.avatar_path,
                "stats": {
                    "likes": likes_count,
                    "dislikes": dislikes_count,
                    "total": likes_count + dislikes_count
                }
            })
    
    return JSONResponse({"is_authenticated": False})


# ========== API ДЛЯ ПРОФИЛЯ ==========

@app.post('/api/profile/update')
async def update_profile(request: Request):
    """Обновление данных профиля"""
    try:
        session_user = get_session_user(request)
        if not session_user:
            return JSONResponse(
                {"success": False, "message": "Требуется авторизация"},
                status_code=401
            )
        
        data = await request.json()
        nickname = data.get('nickname', '').strip()
        new_password = data.get('new_password', '')
        
        # Обновляем профиль
        user_profile = UserProfile.get_or_none(UserProfile.username == session_user["username"])
        if user_profile:
            if nickname:
                user_profile.nickname = nickname
                user_profile.save()
        
        # Обновляем пароль если указан
        if new_password and len(new_password) >= 4:
            auth_user = Avtorization.get_or_none(Avtorization.username == session_user["username"])
            if auth_user:
                auth_user.password = hash_password(new_password)
                auth_user.save()
        
        return JSONResponse({
            "success": True,
            "message": "Профиль успешно обновлен"
        })
        
    except Exception as e:
        print(f"Error in update_profile: {e}")
        return JSONResponse(
            {"success": False, "message": f"Ошибка: {str(e)}"},
            status_code=500
        )


@app.post('/api/profile/avatar')
async def upload_avatar(request: Request, file: UploadFile = File(...)):
    """Загрузка аватара"""
    try:
        session_user = get_session_user(request)
        if not session_user:
            return JSONResponse(
                {"success": False, "message": "Требуется авторизация"},
                status_code=401
            )
        
        # Проверяем тип файла
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if file.content_type not in allowed_types:
            return JSONResponse(
                {"success": False, "message": "Разрешены только изображения (JPEG, PNG, GIF, WEBP)"},
                status_code=400
            )
        
        # Генерируем имя файла
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        avatar_filename = f"{session_user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_extension}"
        avatar_path = AVATARS_DIR / avatar_filename
        
        # Сохраняем файл
        with open(avatar_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Обновляем путь в базе данных
        user_profile = UserProfile.get_or_none(UserProfile.username == session_user["username"])
        if user_profile:
            # Удаляем старый аватар если есть
            if user_profile.avatar_path:
                old_avatar = Path("static") / user_profile.avatar_path.lstrip('/')
                if old_avatar.exists():
                    old_avatar.unlink()
            
            # Сохраняем новый путь
            relative_path = f"/static/avatars/{avatar_filename}"
            user_profile.avatar_path = relative_path
            user_profile.save()
            
            return JSONResponse({
                "success": True,
                "message": "Аватар успешно обновлен",
                "avatar_path": relative_path
            })
        
        return JSONResponse(
            {"success": False, "message": "Профиль не найден"},
            status_code=404
        )
        
    except Exception as e:
        print(f"Error in upload_avatar: {e}")
        return JSONResponse(
            {"success": False, "message": f"Ошибка при загрузке: {str(e)}"},
            status_code=500
        )


@app.delete('/api/profile/avatar')
async def delete_avatar(request: Request):
    """Удаление аватара"""
    try:
        session_user = get_session_user(request)
        if not session_user:
            return JSONResponse(
                {"success": False, "message": "Требуется авторизация"},
                status_code=401
            )
        
        user_profile = UserProfile.get_or_none(UserProfile.username == session_user["username"])
        if user_profile and user_profile.avatar_path:
            # Удаляем файл
            old_avatar = Path("static") / user_profile.avatar_path.lstrip('/')
            if old_avatar.exists():
                old_avatar.unlink()
            
            # Очищаем путь
            user_profile.avatar_path = None
            user_profile.save()
        
        return JSONResponse({
            "success": True,
            "message": "Аватар удален"
        })
        
    except Exception as e:
        print(f"Error in delete_avatar: {e}")
        return JSONResponse(
            {"success": False, "message": f"Ошибка: {str(e)}"},
            status_code=500
        )


@app.post('/api/auth/check-username')
async def check_username(request: Request):
    """Проверка доступности имени пользователя"""
    try:
        data = await request.json()
        username = data.get('username', '').strip()
        
        if len(username) < 3:
            return JSONResponse({
                "available": False,
                "message": "Имя должно быть не менее 3 символов"
            })
        
        existing = Avtorization.get_or_none(Avtorization.username == username)
        
        return JSONResponse({
            "available": existing is None,
            "message": "Имя свободно" if existing is None else "Имя уже занято"
        })
        
    except Exception as e:
        return JSONResponse(
            {"available": False, "message": str(e)},
            status_code=500
        )


# ========== ГЛАВНАЯ СТРАНИЦА ==========

@app.get('/', response_class=HTMLResponse)
async def index(request: Request, q: Optional[str] = None):
    return templates.TemplateResponse(
        request=request, 
        name="index.html",
        context={
            "search_query": q,
            "current_user": get_current_user_context(request)
        }
    )


# Глобальный поиск
@app.get('/search', response_class=HTMLResponse)
async def global_search(request: Request, q: str = Query(..., min_length=1)):
    results = {
        'motivation': [],
        'affirmation': [],
        'funny': [],
        'categories': []
    }
    
    # Поиск в мотивационных цитатах
    mot = Motivation.select().where(
        (Motivation.text.contains(q)) | (Motivation.author.contains(q))
    )
    results['motivation'] = [{
        'id': i.id,
        'text': highlight_text(i.text, q),
        'author': highlight_text(i.author, q) if i.author else '',
        'type': 'Мотивация'
    } for i in mot]
    
    # Поиск в аффирмациях
    aff = Affirmation.select().where(
        (Affirmation.text.contains(q)) | (Affirmation.author.contains(q))
    )
    results['affirmation'] = [{
        'id': i.id,
        'text': highlight_text(i.text, q),
        'author': highlight_text(i.author, q) if i.author else '',
        'type': 'Аффирмация'
    } for i in aff]
    
    # Поиск в смешных цитатах
    fun = FunnyQuote.select().where(
        (FunnyQuote.text.contains(q)) | (FunnyQuote.author.contains(q))
    )
    results['funny'] = [{
        'id': i.id,
        'text': highlight_text(i.text, q),
        'author': highlight_text(i.author, q) if i.author else '',
        'type': 'Юмор'
    } for i in fun]
    
    # Поиск в категориях
    cat = Category.select().where(
        (Category.name.contains(q)) | (Category.description.contains(q))
    )
    results['categories'] = [{
        'id': i.id,
        'name': highlight_text(i.name, q),
        'description': highlight_text(i.description, q) if i.description else '',
    } for i in cat]
    
    total_results = len(results['motivation']) + len(results['affirmation']) + \
                   len(results['funny']) + len(results['categories'])
    
    return templates.TemplateResponse(
        request=request,
        name="search_results.html",
        context={
            "results": results,
            "search_query": q,
            "total_results": total_results,
            "current_user": get_current_user_context(request)
        }
    )


@app.get('/motivation', response_class=HTMLResponse)
async def motivation(
    request: Request,
    search: Optional[str] = None,
    author: Optional[str] = None,
    sort: Optional[str] = None
):
    query = Motivation.select().where(Motivation.is_deleted == False)
    
    if search:
        query = query.where(
            (Motivation.text.contains(search)) | 
            (Motivation.author.contains(search))
        )
    
    if author:
        query = query.where(Motivation.author == author)
    
    all_authors = list(set([m.author for m in Motivation.select().where(Motivation.is_deleted == False) if m.author]))
    all_authors.sort()
    
    if sort:
        if sort == 'author_asc':
            query = query.order_by(Motivation.author.asc())
        elif sort == 'author_desc':
            query = query.order_by(Motivation.author.desc())
        elif sort == 'text_asc':
            query = query.order_by(Motivation.text.asc())
        elif sort == 'text_desc':
            query = query.order_by(Motivation.text.desc())
    
    mot = query
    
    moviv = []
    for i in mot:
        text = i.text
        author_name = i.author
        if search:
            text = highlight_text(text, search)
            author_name = highlight_text(author_name, search) if author_name else ''
        
        moviv.append({
            'id': i.id,
            'text': text,
            'author': author_name,
            'is_deleted': i.is_deleted
        })
    
    total_count = Motivation.select().where(Motivation.is_deleted == False).count()
    
    return templates.TemplateResponse(
        request=request, 
        name="motivation.html", 
        context={
            "quotes": moviv,
            "authors": all_authors,
            "search_query": search,
            "author_filter": author,
            "sort_by": sort or 'default',
            "total_count": total_count,
            "current_user": get_current_user_context(request),
            "quote_type": "motivation"
        }
    )


@app.get('/affirmation', response_class=HTMLResponse)
async def affirmation(
    request: Request,
    search: Optional[str] = None,
    author: Optional[str] = None,
    sort: Optional[str] = None
):
    query = Affirmation.select().where(Affirmation.is_deleted == False)
    
    if search:
        query = query.where(
            (Affirmation.text.contains(search)) | 
            (Affirmation.author.contains(search))
        )
    
    if author:
        query = query.where(Affirmation.author == author)
    
    all_authors = list(set([a.author for a in Affirmation.select().where(Affirmation.is_deleted == False) if a.author]))
    all_authors.sort()
    
    if sort:
        if sort == 'author_asc':
            query = query.order_by(Affirmation.author.asc())
        elif sort == 'author_desc':
            query = query.order_by(Affirmation.author.desc())
        elif sort == 'text_asc':
            query = query.order_by(Affirmation.text.asc())
        elif sort == 'text_desc':
            query = query.order_by(Affirmation.text.desc())
    
    aff = query
    
    affir = []
    for i in aff:
        text = i.text
        author_name = i.author
        if search:
            text = highlight_text(text, search)
            author_name = highlight_text(author_name, search) if author_name else ''
        
        affir.append({
            'id': i.id,
            'text': text,
            'author': author_name,
            'is_deleted': i.is_deleted
        })
    
    total_count = Affirmation.select().where(Affirmation.is_deleted == False).count()
    
    return templates.TemplateResponse(
        request=request, 
        name="affirmation.html", 
        context={
            "quotes": affir,
            "authors": all_authors,
            "search_query": search,
            "author_filter": author,
            "sort_by": sort or 'default',
            "total_count": total_count,
            "current_user": get_current_user_context(request),
            "quote_type": "affirmation"
        }
    )


@app.get('/funny', response_class=HTMLResponse)
async def funny(
    request: Request,
    search: Optional[str] = None,
    author: Optional[str] = None,
    sort: Optional[str] = None
):
    query = FunnyQuote.select().where(FunnyQuote.is_deleted == False)
    
    if search:
        query = query.where(
            (FunnyQuote.text.contains(search)) | 
            (FunnyQuote.author.contains(search))
        )
    
    if author:
        query = query.where(FunnyQuote.author == author)
    
    all_authors = list(set([f.author for f in FunnyQuote.select().where(FunnyQuote.is_deleted == False) if f.author]))
    all_authors.sort()
    
    if sort:
        if sort == 'author_asc':
            query = query.order_by(FunnyQuote.author.asc())
        elif sort == 'author_desc':
            query = query.order_by(FunnyQuote.author.desc())
        elif sort == 'text_asc':
            query = query.order_by(FunnyQuote.text.asc())
        elif sort == 'text_desc':
            query = query.order_by(FunnyQuote.text.desc())
    
    fun = query
    
    funny_quotes = []
    for i in fun:
        text = i.text
        author_name = i.author
        if search:
            text = highlight_text(text, search)
            author_name = highlight_text(author_name, search) if author_name else ''
        
        funny_quotes.append({
            'id': i.id,
            'text': text,
            'author': author_name,
            'is_deleted': i.is_deleted
        })
    
    total_count = FunnyQuote.select().where(FunnyQuote.is_deleted == False).count()
    
    return templates.TemplateResponse(
        request=request, 
        name="funny.html", 
        context={
            "quotes": funny_quotes,
            "authors": all_authors,
            "search_query": search,
            "author_filter": author,
            "sort_by": sort or 'default',
            "total_count": total_count,
            "current_user": get_current_user_context(request),
            "quote_type": "funny"
        }
    )


@app.get('/category', response_class=HTMLResponse)
async def category(
    request: Request,
    search: Optional[str] = None,
    sort: Optional[str] = None
):
    query = Category.select().where(Category.is_deleted == False)
    
    if search:
        query = query.where(
            (Category.name.contains(search)) | 
            (Category.description.contains(search))
        )
    
    if sort:
        if sort == 'name_asc':
            query = query.order_by(Category.name.asc())
        elif sort == 'name_desc':
            query = query.order_by(Category.name.desc())
        elif sort == 'date_asc':
            query = query.order_by(Category.created_at.asc())
        elif sort == 'date_desc':
            query = query.order_by(Category.created_at.desc())
    
    cat = query
    
    categories = []
    for i in cat:
        name = i.name
        description = i.description
        if search:
            name = highlight_text(name, search)
            description = highlight_text(description, search) if description else ''
        
        categories.append({
            'id': i.id,
            'name': name,
            'description': description,
            'created_at': i.created_at,
            'is_deleted': i.is_deleted
        })
    
    total_count = Category.select().where(Category.is_deleted == False).count()
    
    return templates.TemplateResponse(
        request=request, 
        name="category.html", 
        context={
            "categories": categories,
            "search_query": search,
            "sort_by": sort or 'default',
            "total_count": total_count,
            "current_user": get_current_user_context(request)
        }
    )


@app.get('/categoryquote', response_class=HTMLResponse)
async def category_q(
    request: Request, 
    id: int = None,
    search: Optional[str] = None,
    quote_type: Optional[str] = None,
    sort: Optional[str] = None
):
    if id is None:
        return templates.TemplateResponse(
            request=request, 
            name="categoryquote.html", 
            context={
                "category_quotes": [], 
                "category": None,
                "current_user": get_current_user_context(request)
            }
        )
    
    category = Category.get_or_none(Category.id == id)
    
    query = CategoryQuote.select().where(CategoryQuote.category_id == id)
    
    if search:
        query = query.where(
            (CategoryQuote.quote_text.contains(search)) | 
            (CategoryQuote.quote_author.contains(search))
        )
    
    if quote_type:
        query = query.where(CategoryQuote.quote_type == quote_type)
    
    all_types = list(set([q.quote_type for q in CategoryQuote.select().where(CategoryQuote.category_id == id)]))
    all_types.sort()
    
    if sort:
        if sort == 'author_asc':
            query = query.order_by(CategoryQuote.quote_author.asc())
        elif sort == 'author_desc':
            query = query.order_by(CategoryQuote.quote_author.desc())
        elif sort == 'text_asc':
            query = query.order_by(CategoryQuote.quote_text.asc())
        elif sort == 'text_desc':
            query = query.order_by(CategoryQuote.quote_text.desc())
        elif sort == 'date_asc':
            query = query.order_by(CategoryQuote.added_at.asc())
        elif sort == 'date_desc':
            query = query.order_by(CategoryQuote.added_at.desc())
    
    cat_q = query
    
    category_quotes = []
    for i in cat_q:
        text = i.quote_text
        author = i.quote_author
        if search:
            text = highlight_text(text, search)
            author = highlight_text(author, search) if author else ''
        
        category_quotes.append({
            'id': i.id,
            'category_id': i.category_id,
            'quote_type': i.quote_type,
            'quote_text': text,
            'added_at': i.added_at,
            'quote_author': author
        })
    
    total_count = CategoryQuote.select().where(CategoryQuote.category_id == id).count()
    
    return templates.TemplateResponse(
        request=request, 
        name="categoryquote.html", 
        context={
            "category_quotes": category_quotes,
            "category": {
                "id": category.id if category else None,
                "name": category.name if category else "Неизвестная категория",
                "description": category.description if category else ""
            } if category else None,
            "search_query": search,
            "quote_type_filter": quote_type,
            "quote_types": all_types,
            "sort_by": sort or 'default',
            "total_count": total_count,
            "current_user": get_current_user_context(request)
        }
    )


@app.get('/reaction', response_class=HTMLResponse)
async def reaction(request: Request):
    react = UserReaction.select().order_by(UserReaction.created_at.desc())
    reactions = [{
        'id': i.id,
        'username': i.username,
        'quote_id': i.quote_id,
        'quote_type': i.quote_type,
        'reaction': i.reaction,
        'created_at': i.created_at
    } for i in react]
    return templates.TemplateResponse(
        request=request, 
        name="reaction.html", 
        context={
            "reactions": reactions,
            "current_user": get_current_user_context(request)
        }
    )


@app.get('/profile', response_class=HTMLResponse)
async def profile(request: Request):
    current_user = get_current_user_context(request)
    if not current_user.get("is_authenticated"):
        return RedirectResponse(url='/')
    
    prof = UserProfile.select().where(UserProfile.username == current_user["username"])
    profiles = [{
        'id': i.id,
        'username': i.username,
        'nickname': i.nickname,
        'avatar_path': i.avatar_path,
        'created_at': i.created_at
     } for i in prof]
    
    # Получаем историю реакций пользователя
    user_reactions = UserReaction.select().where(
        UserReaction.username == current_user["username"]
    ).order_by(UserReaction.created_at.desc()).limit(10)
    
    reactions_history = []
    for r in user_reactions:
        quote_text = ""
        if r.quote_type == 'motivation':
            quote = Motivation.get_or_none(Motivation.id == r.quote_id)
            quote_text = quote.text[:100] + "..." if quote else "Цитата удалена"
        elif r.quote_type == 'affirmation':
            quote = Affirmation.get_or_none(Affirmation.id == r.quote_id)
            quote_text = quote.text[:100] + "..." if quote else "Цитата удалена"
        elif r.quote_type == 'funny':
            quote = FunnyQuote.get_or_none(FunnyQuote.id == r.quote_id)
            quote_text = quote.text[:100] + "..." if quote else "Цитата удалена"
        
        reactions_history.append({
            'quote_text': quote_text,
            'reaction': r.reaction,
            'created_at': r.created_at
        })
    
    return templates.TemplateResponse(
        request=request, 
        name="profile.html", 
        context={
            "profiles": profiles,
            "current_user": current_user,
            "reactions_history": reactions_history
        }
    )


# ========== РЕЖИМ ТИШИНЫ (ZEN MODE) ==========

@app.get('/zen/{quote_type}', response_class=HTMLResponse)
async def zen_mode(
    request: Request,
    quote_type: str,
    id: Optional[int] = None
):
    models = {
        'motivation': (Motivation, 'Мотивация'),
        'affirmation': (Affirmation, 'Аффирмация'),
        'funny': (FunnyQuote, 'Юмор')
    }
    
    if quote_type not in models:
        return RedirectResponse(url='/')
    
    ModelClass, type_name = models[quote_type]
    
    all_quotes = list(ModelClass.select().where(ModelClass.is_deleted == False))
    quotes_data = [quote_to_dict(q, quote_type) for q in all_quotes]
    
    selected_quote = None
    if id:
        quote_obj = ModelClass.get_or_none((ModelClass.id == id) & (ModelClass.is_deleted == False))
        if quote_obj:
            selected_quote = quote_to_dict(quote_obj, quote_type)
    
    return templates.TemplateResponse(
        request=request,
        name="zen_mode.html",
        context={
            "quote_type": quote_type,
            "type_name": type_name,
            "all_quotes": quotes_data,
            "selected_quote": selected_quote,
            "current_user": get_current_user_context(request)
        }
    )


# ========== API ДЛЯ РЕАКЦИЙ ==========

@app.post('/api/reaction')
async def add_reaction(request: Request):
    try:
        data = await request.json()
        quote_id = data.get('quote_id')
        quote_type = data.get('quote_type')
        reaction_type = data.get('reaction')
        
        session_user = get_session_user(request)
        if not session_user:
            return JSONResponse(
                {"error": "Требуется авторизация", "redirect": True}, 
                status_code=401
            )
        
        username = session_user["username"]
        
        if not all([quote_id, quote_type, reaction_type]):
            return JSONResponse(
                {"error": "Missing required fields"}, 
                status_code=400
            )
        
        existing = UserReaction.get_or_none(
            (UserReaction.username == username) &
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type)
        )
        
        if existing:
            if existing.reaction == reaction_type:
                existing.delete_instance()
                user_reaction = None
            else:
                existing.reaction = reaction_type
                existing.created_at = datetime.now()
                existing.save()
                user_reaction = reaction_type
        else:
            UserReaction.create(
                username=username,
                quote_id=quote_id,
                quote_type=quote_type,
                reaction=reaction_type
            )
            user_reaction = reaction_type
        
        likes_count = UserReaction.select().where(
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type) &
            (UserReaction.reaction == 'like')
        ).count()
        
        dislikes_count = UserReaction.select().where(
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type) &
            (UserReaction.reaction == 'dislike')
        ).count()
        
        return JSONResponse({
            "success": True,
            "likes_count": likes_count,
            "dislikes_count": dislikes_count,
            "user_reaction": user_reaction
        })
        
    except Exception as e:
        print(f"Error in add_reaction: {e}")
        return JSONResponse(
            {"error": str(e)}, 
            status_code=500
        )


@app.get('/api/reactions/count')
async def get_reactions_count(
    quote_id: int = Query(...),
    quote_type: str = Query(...)
):
    try:
        likes_count = UserReaction.select().where(
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type) &
            (UserReaction.reaction == 'like')
        ).count()
        
        dislikes_count = UserReaction.select().where(
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type) &
            (UserReaction.reaction == 'dislike')
        ).count()
        
        return JSONResponse({
            "likes": likes_count,
            "dislikes": dislikes_count
        })
        
    except Exception as e:
        print(f"Error in get_reactions_count: {e}")
        return JSONResponse(
            {"error": str(e)}, 
            status_code=500
        )


@app.get('/api/reactions/user')
async def get_user_reaction(
    request: Request,
    quote_id: int = Query(...),
    quote_type: str = Query(...)
):
    session_user = get_session_user(request)
    if not session_user:
        return JSONResponse({"user_reaction": None})
    
    try:
        reaction = UserReaction.get_or_none(
            (UserReaction.username == session_user["username"]) &
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type)
        )
        
        return JSONResponse({
            "user_reaction": reaction.reaction if reaction else None
        })
        
    except Exception as e:
        print(f"Error in get_user_reaction: {e}")
        return JSONResponse(
            {"error": str(e)}, 
            status_code=500
        )


@app.get('/api/reactions/all')
async def get_all_reactions():
    try:
        reactions = UserReaction.select().order_by(UserReaction.created_at.desc())
        
        result = []
        for r in reactions:
            quote_text = ""
            if r.quote_type == 'motivation':
                quote = Motivation.get_or_none(Motivation.id == r.quote_id)
                quote_text = quote.text[:50] + "..." if quote else "Цитата удалена"
            elif r.quote_type == 'affirmation':
                quote = Affirmation.get_or_none(Affirmation.id == r.quote_id)
                quote_text = quote.text[:50] + "..." if quote else "Цитата удалена"
            elif r.quote_type == 'funny':
                quote = FunnyQuote.get_or_none(FunnyQuote.id == r.quote_id)
                quote_text = quote.text[:50] + "..." if quote else "Цитата удалена"
            
            result.append({
                'id': r.id,
                'username': r.username,
                'quote_id': r.quote_id,
                'quote_type': r.quote_type,
                'quote_text': quote_text,
                'reaction': r.reaction,
                'created_at': r.created_at.isoformat() if r.created_at else None
            })
        
        return JSONResponse({"reactions": result})
        
    except Exception as e:
        print(f"Error in get_all_reactions: {e}")
        return JSONResponse(
            {"error": str(e)}, 
            status_code=500
        )


@app.delete('/api/reaction')
async def delete_reaction(request: Request):
    try:
        data = await request.json()
        quote_id = data.get('quote_id')
        quote_type = data.get('quote_type')
        
        session_user = get_session_user(request)
        if not session_user:
            return JSONResponse(
                {"error": "Требуется авторизация"}, 
                status_code=401
            )
        
        username = session_user["username"]
        
        if not all([quote_id, quote_type]):
            return JSONResponse(
                {"error": "Missing required fields"}, 
                status_code=400
            )
        
        reaction = UserReaction.get_or_none(
            (UserReaction.username == username) &
            (UserReaction.quote_id == quote_id) &
            (UserReaction.quote_type == quote_type)
        )
        
        if reaction:
            reaction.delete_instance()
            
            likes_count = UserReaction.select().where(
                (UserReaction.quote_id == quote_id) &
                (UserReaction.quote_type == quote_type) &
                (UserReaction.reaction == 'like')
            ).count()
            
            dislikes_count = UserReaction.select().where(
                (UserReaction.quote_id == quote_id) &
                (UserReaction.quote_type == quote_type) &
                (UserReaction.reaction == 'dislike')
            ).count()
            
            return JSONResponse({
                "success": True,
                "message": "Reaction deleted",
                "likes_count": likes_count,
                "dislikes_count": dislikes_count
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Reaction not found"
            }, status_code=404)
        
    except Exception as e:
        print(f"Error in delete_reaction: {e}")
        return JSONResponse(
            {"error": str(e)}, 
            status_code=500
        )