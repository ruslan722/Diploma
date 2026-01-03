from peewee import (
    Model, MySQLDatabase, CharField, DateTimeField, BooleanField, TextField, IntegerField
)
import datetime
import logging

# Настройка БД (убедитесь, что параметры подключения верны)
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
    is_deleted = BooleanField(default=False)  # Мягкое удаление

class Affirmation(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()
    is_deleted = BooleanField(default=False)  # Мягкое удаление

class FunnyQuote(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()
    is_deleted = BooleanField(default=False)  # Мягкое удаление

class Avtorization(BaseModel):
    username = CharField(unique=True)
    password = CharField() # Пароль уже хранится как хэш в вашем коде
    role = CharField(default='пользователь')
    is_main_admin = BooleanField(default=False)

class AdminRequests(BaseModel):
    username = CharField()
    request_date = DateTimeField(default=datetime.datetime.now)
    status = CharField(default='ожидание')
    reviewed_by = CharField(null=True)
    admin_token = TextField(null=True)


# --- НОВЫЕ ТАБЛИЦЫ ---

class UserReaction(BaseModel):
    username = CharField()
    quote_id = IntegerField()
    quote_type = CharField() # 'motivation', 'affirmation', 'funny'
    reaction = CharField()   # 'like' или 'dislike'

    class Meta:
        indexes = (
            # Уникальный индекс, чтобы один юзер мог поставить только 1 реакцию на 1 цитату
            (('username', 'quote_id', 'quote_type'), True),
        )

class UserProfile(BaseModel):
    username = CharField(unique=True)
    nickname = CharField(default='')  # Отображаемое имя
    avatar_path = CharField(default='')  # Путь к аватарке
    created_at = DateTimeField(default=datetime.datetime.now)

class AdminActionLog(BaseModel):
    admin_username = CharField()
    action_type = CharField()  # 'add_quote', 'edit_quote', 'delete_quote', etc.
    target_username = CharField()
    details = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)


# Инициализация и миграция (добавление колонок, если их нет)
def init_db():
    db.connect()
    # Создаем таблицы
    db.create_tables([
        Motivation, Affirmation, FunnyQuote, Avtorization,
        AdminRequests, UserReaction, UserProfile, AdminActionLog
    ], safe=True)
    
    # Простая миграция для добавления колонок в существующие таблицы
    try:
        from playhouse.migrate import MySQLMigrator, migrate
        migrator = MySQLMigrator(db)
        
        # Добавляем is_deleted, если его нет
        try:
            migrate(migrator.add_column('motivation', 'is_deleted', BooleanField(default=False)))
        except: pass
        try:
            migrate(migrator.add_column('affirmation', 'is_deleted', BooleanField(default=False)))
        except: pass
        try:
            migrate(migrator.add_column('funnyquote', 'is_deleted', BooleanField(default=False)))
        except: pass
            
    except Exception as e:
        print(f"Migration info: {e}")

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
    
    db.close()

if __name__ == "__main__":
    init_db()