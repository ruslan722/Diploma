from peewee import (
    Model, MySQLDatabase, CharField
)

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

class Affirmation(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()

class FunnyQuote(BaseModel):
    text = CharField(max_length=512, unique=True)
    author = CharField()

class Avtorization(BaseModel):
    username = CharField()
    password = CharField()
    role = CharField(default='user')

db.connect()
db.create_tables([Motivation, Affirmation, FunnyQuote, Avtorization], safe=True)
db.close()
