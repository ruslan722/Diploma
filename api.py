from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse


from connect import Motivation, Affirmation, FunnyQuote, Avtorization, \
UserReaction, UserProfile, Category, CategoryQuote



app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get('/motivation', response_class=HTMLResponse)
async def motivation(request: Request):
    mot = Motivation.select()
    moviv = [{
        'id': i.id,
        'text': i.text,
        'author': i.author,
        'is_deleted' : i.is_deleted
    } for i in mot]
    return templates.TemplateResponse("motivation.html",
                                       {"request": request, 
                                        "quotes": moviv})

@app.get('/affirmation', response_class=HTMLResponse)
async def affirmation(request: Request):
    aff = Affirmation.select()
    affir = [{
        'id' : i.id,
        'text': i.text,
        'author': i.author,
        'is_deleted' : i.is_deleted
    } for i in aff]
    return templates.TemplateResponse("affirmation.html",
                                       {"request": request,
                                        "quotes": affir})

@app.get('/funny', response_class=HTMLResponse)
async def funny(request: Request):
    fun = FunnyQuote.select()
    funnies = [{
        'id' : i.id,
        'text': i.text,
        'author': i.author,
        'is_deleted' : i.is_deleted
    } for i in fun]
    return templates.TemplateResponse("funny.html",
                                       {"request": request,
                                        "quotes": funnies})

@app.get('/avtorization')
async def avtorization():
    avt = Avtorization.select()
    return [{
        'id' : i.id,
        'username' : i.username,
        'password' : i.password,
        'role' : i.role,
        'is_main_admin' : i.is_main_admin
    } for i in avt]

@app.get('/reaction', response_class=HTMLResponse)
async def reaction(request: Request):
    react = UserReaction.select()
    reactions = [{
        'id' : i.id,
        'username' : i.username,
        'quote_id' : i.quote_id,
        'quote_type' : i.quote_type,
        'reaction' : i.reaction
     } for i in react]
    return templates.TemplateResponse("reaction.html",
                                       {"request": request,
                                        "reactions": reactions})

@app.get('/profile', response_class=HTMLResponse)
async def profile(request: Request):
    prof = UserProfile.select()
    profiles = [{
        'id' : i.id,
        'username': i.username,
        'nickname' : i.nickname,
        'avatar_path' : i.avatar_path,
        'created_at' : i.created_at
     } for i in prof]
    return templates.TemplateResponse("profile.html",
                                       {"request": request,
                                        "profiles": profiles})

@app.get('/category', response_class=HTMLResponse)
async def category(request: Request):
    cat = Category.select()
    categories =  [{ 
        'id' : i.id,
        'name' : i.name,
        'description' : i.description,
        'created_at' : i.created_at,
        'is_deleted' : i.is_deleted

    } for i in cat]
    return templates.TemplateResponse("category.html",
                                       {"request": request,
                                        "categories": categories})

@app.get('/categoryquote', response_class=HTMLResponse)
async def category_q(request: Request):
    cat_q = CategoryQuote.select()
    category_quotes = [{
        'id' : i.id,
        'category_id' : i.category,
        'quote_type' : i.quote_type,
        'quote_text' : i.quote_text,
        'quote_author' : i.quote_author,
        'added_at' : i.added_at

    } for i in cat_q]
    return templates.TemplateResponse("categoryquote.html",
                                       {"request": request,
                                        "category_quotes": category_quotes})