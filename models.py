import datetime
import uuid
from peewee import *
from app import db
from playhouse.sqlite_ext import JSONField 

class Conversation(db.Model):
    call_sid = CharField(max_length=100, primary_key=True, index=True)
    call_country = CharField(max_length=10, default='')
    call_zip = CharField(max_length=10, default='')
    call_state = CharField(max_length=10, index=True, default='')
    call_city = CharField(max_length=100, index=True, default='')
    call_number = CharField(max_length=20, default='')
    context = JSONField(null=True)
    last_update = DateTimeField(default=datetime.datetime.now)

def create_tables():
    Conversation.create_table()

