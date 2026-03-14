from fastapi import FastAPI
from connect import Motivation, Affirmation, FunnyQuote, Avtorization, \
UserReaction, UserProfile, Category



app = FastAPI()

@app.get('/motivation')
async def motivation():
    mot = Motivation.select()
    return [{
        'id': i.id,
        'text': i.text,
        'author': i.author,
        'is_deleted' : i.is_deleted
    } for i in mot]

@app.get('/affirmation')
async def affirmation():
    aff = Affirmation.select()
    return [{
        'id' : i.id,
        'text': i.text,
        'author': i.author,
        'is_deleted' : i.is_deleted
    } for i in aff]

@app.get('/funny')
async def funny():
    fun = FunnyQuote.select()
    return [{
        'id' : i.id,
        'text': i.text,
        'author': i.author,
        'is_deleted' : i.is_deleted
    } for i in fun]

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

@app.get('/reaction')
async def reaction():
    react = UserReaction.select()
    return [{
        'id' : i.id,
        'username' : i.username,
        'quote_id' : i.quote_id,
        'quote_type' : i.quote_type,
        'reaction' : i.reaction
     } for i in react]

@app.get('/profile')
async def profile():
    prof = UserProfile.select()
    return [{
        'id' : i.id,
        'username': i.username,
        'nickname' : i.nickname,
        'avatar_path' : i.avatar_path,
        'created_at' : i.created_at
     } for i in prof]
@app.get('/category')
async def category():
    cat = Category.select()
    return [{
        'id' : i.id,
        'name' : i.name,
        'description' : i.description,
        'created_at' : i.created_at,
        'is_deleted' : i.is_deleted

    }for i in cat]