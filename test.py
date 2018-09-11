from peewee import *

db = SqliteDatabase('teams.db')

class Team(Model):
    number = IntegerField(3, primary_key=True, unique=True)
    data = CharField(255)

    class Meta:
        database = db  # модель будет использовать базу данных 'people.db'

Team.create_table()

for person in Team.select():
	print(person.data)
