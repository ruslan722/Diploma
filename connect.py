from peewee import (
    Model, MySQLDatabase, CharField, DateTimeField, BooleanField, TextField, IntegerField, ForeignKeyField, FloatField
)
import datetime
import logging


db = MySQLDatabase(
    'motivation',
    user='root',
    password='root',
    host='localhost',
    port=3306
)

class BaseModel(Model):
    class Meta:
        database = db

class Motivation(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()
    is_deleted = BooleanField(default=False)  

class Affirmation(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()
    is_deleted = BooleanField(default=False)

class FunnyQuote(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()
    is_deleted = BooleanField(default=False)

class Avtorization(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    role = CharField(default='пользователь')
    is_main_admin = BooleanField(default=False)

class AdminRequests(BaseModel):
    username = CharField()
    request_date = DateTimeField(default=datetime.datetime.now)
    status = CharField(default='ожидание')
    reviewed_by = CharField(null=True)
    admin_token = TextField(null=True)


# --- ТАБЛИЦЫ ДЛЯ РЕАКЦИЙ И ПРОФИЛЕЙ ---

class UserReaction(BaseModel):
    username = CharField()
    quote_id = IntegerField()
    quote_type = CharField()
    reaction = CharField()
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        indexes = (
            (('username', 'quote_id', 'quote_type'), True),
        )

class UserProfile(BaseModel):
    username = CharField(unique=True)
    nickname = CharField(default='')
    avatar_path = CharField(default='', null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class AdminActionLog(BaseModel):
    admin_username = CharField()
    action_type = CharField()
    target_username = CharField()
    details = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)


# --- ТАБЛИЦЫ ДЛЯ КАТЕГОРИЙ ---

class Category(BaseModel):
    """Категория для группировки цитат"""
    name = CharField(unique=True, max_length=100)
    description = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    is_deleted = BooleanField(default=False)
    
    class Meta:
        table_name = 'categories'

class CategoryQuote(BaseModel):
    """Связь цитаты с категорией"""
    category = ForeignKeyField(Category, backref='quotes', on_delete='CASCADE')
    quote_type = CharField(max_length=20)
    quote_text = TextField()
    quote_author = CharField(max_length=200)
    added_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        table_name = 'category_quotes'
        indexes = (
            (('category', 'quote_type'), False),
        )


# --- ТАБЛИЦЫ ДЛЯ РЕЙТИНГА ---

class QuoteRating(BaseModel):
    """Рейтинг цитаты (1-5 звезд)"""
    quote_id = IntegerField()
    quote_type = CharField(max_length=20)
    total_rating = IntegerField(default=0)
    votes_count = IntegerField(default=0)
    average_rating = FloatField(default=0.0)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        table_name = 'quoterating'
        indexes = (
            (('quote_id', 'quote_type'), True),
        )

class UserQuoteRating(BaseModel):
    """Оценка пользователя для конкретной цитаты"""
    username = CharField()
    quote_id = IntegerField()
    quote_type = CharField(max_length=20)
    rating = IntegerField()
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        table_name = 'userquoterating'
        indexes = (
            (('username', 'quote_id', 'quote_type'), True),
        )


def init_db():
    db.connect()
    
    # Создаем все таблицы
    db.create_tables([
        Motivation,
        Affirmation,
        FunnyQuote,
        Avtorization,
        AdminRequests,
        UserReaction,
        UserProfile,
        AdminActionLog,
        Category,
        CategoryQuote,
        QuoteRating,
        UserQuoteRating
    ], safe=True)
    
    # Создание админа
    def hash_password(password):
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    try:
        Avtorization.get(Avtorization.username == "admin")
    except Avtorization.DoesNotExist:
        Avtorization.create(
            username="admin",
            password=hash_password("admin"),
            role='администратор',
            is_main_admin=True
        )
        try:
            UserProfile.get(UserProfile.username == "admin")
        except UserProfile.DoesNotExist:
            UserProfile.create(
                username="admin",
                nickname="Администратор",
                avatar_path=None
            )
    
    db.close()

if __name__ == "__main__":
    init_db()