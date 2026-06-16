from peewee import (
    Model, MySQLDatabase, CharField, DateTimeField, BooleanField, TextField, IntegerField, ForeignKeyField, FloatField
)
import datetime
import logging
import os
import json
import re

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

class Category(BaseModel):
    name = CharField(unique=True, max_length=100)
    description = TextField(null=True)
    created_by = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    is_deleted = BooleanField(default=False)
    
    class Meta:
        table_name = 'categories'

class CategoryQuote(BaseModel):
    category = ForeignKeyField(Category, backref='quotes', on_delete='CASCADE')
    quote_type = CharField(max_length=20)
    quote_text = TextField()
    quote_author = CharField(max_length=200)
    added_by = CharField(null=True)
    added_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        table_name = 'category_quotes'
        indexes = (
            (('category', 'quote_type'), False),
        )

class QuoteRating(BaseModel):
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


def cleanup_duplicate_category_quotes():
    try:
        db.connect()
        
        from peewee import fn
        
        duplicates = (CategoryQuote
                      .select(CategoryQuote.category, CategoryQuote.quote_text, CategoryQuote.quote_type, fn.COUNT(CategoryQuote.id).alias('count'))
                      .group_by(CategoryQuote.category, CategoryQuote.quote_text, CategoryQuote.quote_type)
                      .having(fn.COUNT(CategoryQuote.id) > 1))
        
        deleted_count = 0
        for dup in duplicates:
            dup_quotes = CategoryQuote.select().where(
                (CategoryQuote.category == dup.category) &
                (CategoryQuote.quote_text == dup.quote_text) &
                (CategoryQuote.quote_type == dup.quote_type)
            ).order_by(CategoryQuote.id)
            
            first = True
            for quote in dup_quotes:
                if not first:
                    quote.delete_instance()
                    deleted_count += 1
                first = False
        
        text_duplicates = (CategoryQuote
                          .select(CategoryQuote.quote_text, CategoryQuote.quote_type, fn.COUNT(CategoryQuote.id).alias('count'))
                          .group_by(CategoryQuote.quote_text, CategoryQuote.quote_type)
                          .having(fn.COUNT(CategoryQuote.id) > 1))
        
        for dup in text_duplicates:
            dup_quotes = CategoryQuote.select().where(
                (CategoryQuote.quote_text == dup.quote_text) &
                (CategoryQuote.quote_type == dup.quote_type)
            ).order_by(CategoryQuote.id)
            
            first = True
            for quote in dup_quotes:
                if not first:
                    quote.delete_instance()
                    deleted_count += 1
                first = False
        
        if deleted_count > 0:
            logging.info(f"Удалено дубликатов цитат из категорий: {deleted_count}")
        
        db.close()
        return deleted_count
    except Exception as e:
        logging.error(f"Ошибка очистки дубликатов: {e}")
        if not db.is_closed():
            db.close()
        return 0


def sync_categories_to_file():
    try:
        categories = Category.select().where(Category.is_deleted == False)
        
        categories_data = []
        for cat in categories:
            quotes = CategoryQuote.select().where(CategoryQuote.category == cat.id)
            mot_count = sum(1 for q in quotes if q.quote_type == 'motivation')
            aff_count = sum(1 for q in quotes if q.quote_type == 'affirmation')
            fun_count = sum(1 for q in quotes if q.quote_type == 'funny')
            
            if mot_count >= aff_count and mot_count >= fun_count:
                cat_type = "motivation"
            elif aff_count >= mot_count and aff_count >= fun_count:
                cat_type = "affirmation"
            else:
                cat_type = "funny"
            
            categories_data.append({
                "name": cat.name,
                "description": cat.description if cat.description else "",
                "type": cat_type
            })
        
        categories_file_path = 'categories.py'
        
        if os.path.exists(categories_file_path):
            with open(categories_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            pattern = r'categories_data\s*=\s*\[(.*?)\]'
            
            new_categories_str = "categories_data = [\n"
            for cat in categories_data:
                new_categories_str += f'    {{\n'
                new_categories_str += f'        "name": "{cat["name"]}",\n'
                new_categories_str += f'        "description": "{cat["description"]}",\n'
                new_categories_str += f'        "type": "{cat["type"]}"\n'
                new_categories_str += f'    }},\n'
            new_categories_str += ']\n'
            
            if re.search(pattern, content, re.DOTALL):
                new_content = re.sub(pattern, new_categories_str.rstrip('\n'), content, flags=re.DOTALL)
            else:
                new_content = content + '\n\n' + new_categories_str
            
            with open(categories_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logging.info("Файл categories.py успешно синхронизирован")
            return True
        else:
            logging.warning("Файл categories.py не найден")
            return False
            
    except Exception as e:
        logging.error(f"Ошибка синхронизации categories.py: {e}")
        return False


def sync_quotes_to_categories_file():
    try:
        categories_file_path = 'categories.py'
        
        if not os.path.exists(categories_file_path):
            return False
        
        with open(categories_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        existing_category_quotes = {}
        
        pattern = r'CATEGORY_QUOTES\s*=\s*(\{.*?\})\n'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                import ast
                existing_data_str = match.group(1)
                existing_data = ast.literal_eval(existing_data_str)
                if isinstance(existing_data, dict):
                    existing_category_quotes = existing_data
            except:
                pass
        
        category_quotes = {}
        category_relations = CategoryQuote.select()
        
        for rel in category_relations:
            try:
                category = Category.get_by_id(rel.category)
                if category.name not in category_quotes:
                    category_quotes[category.name] = []
                
                escaped_text = rel.quote_text.replace('"', '\\"')
                escaped_author = rel.quote_author.replace('"', '\\"') if rel.quote_author else ""
                
                quote_item = {
                    "text": escaped_text,
                    "author": escaped_author,
                    "type": rel.quote_type
                }
                
                is_duplicate = False
                if category.name in existing_category_quotes:
                    for existing_quote in existing_category_quotes[category.name]:
                        if (existing_quote.get('text') == escaped_text and 
                            existing_quote.get('type') == rel.quote_type):
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    category_quotes[category.name].append(quote_item)
                    
            except Category.DoesNotExist:
                continue
        
        for cat_name, existing_quotes in existing_category_quotes.items():
            if cat_name not in category_quotes:
                category_quotes[cat_name] = []
            
            for existing_quote in existing_quotes:
                is_in_db = False
                for rel in category_relations:
                    try:
                        category = Category.get_by_id(rel.category)
                        if (category.name == cat_name and 
                            rel.quote_text == existing_quote.get('text') and
                            rel.quote_type == existing_quote.get('type')):
                            is_in_db = True
                            break
                    except:
                        pass
                
                if not is_in_db:
                    is_dup_in_new = False
                    for new_quote in category_quotes[cat_name]:
                        if (new_quote.get('text') == existing_quote.get('text') and
                            new_quote.get('type') == existing_quote.get('type')):
                            is_dup_in_new = True
                            break
                    
                    if not is_dup_in_new:
                        category_quotes[cat_name].append(existing_quote)
        
        quotes_by_category_str = "\n\n# Категории с цитатами (автоматически синхронизировано)\n"
        quotes_by_category_str += "CATEGORY_QUOTES = {\n"
        
        for cat_name, quotes in category_quotes.items():
            quotes_by_category_str += f'    "{cat_name}": [\n'
            for quote in quotes:
                quotes_by_category_str += f'        {{\n'
                quotes_by_category_str += f'            "text": "{quote["text"]}",\n'
                quotes_by_category_str += f'            "author": "{quote["author"]}",\n'
                quotes_by_category_str += f'            "type": "{quote["type"]}"\n'
                quotes_by_category_str += f'        }},\n'
            quotes_by_category_str += '    ],\n'
        
        quotes_by_category_str += '}\n'
        
        pattern_full = r'CATEGORY_QUOTES\s*=\s*\{.*?\}\n'
        
        if re.search(pattern_full, content, re.DOTALL):
            new_content = re.sub(pattern_full, quotes_by_category_str, content, flags=re.DOTALL)
        else:
            new_content = content + quotes_by_category_str
        
        with open(categories_file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logging.info("Цитаты категорий синхронизированы в categories.py без дублирования")
        return True
        
    except Exception as e:
        logging.error(f"Ошибка синхронизации цитат в categories.py: {e}")
        return False


def check_quote_in_any_category(quote_text, quote_type, exclude_category_id=None):
    try:
        query = CategoryQuote.select().where(
            (CategoryQuote.quote_text == quote_text) &
            (CategoryQuote.quote_type == quote_type)
        )
        
        if exclude_category_id:
            query = query.where(CategoryQuote.category != exclude_category_id)
        
        existing = query.first()
        
        if existing:
            try:
                category = Category.get_by_id(existing.category)
                return True, category.name
            except:
                return True, "неизвестной категории"
        return False, None
    except Exception as e:
        logging.error(f"Ошибка проверки цитаты: {e}")
        return False, None


def init_db():
    db.connect()
    
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