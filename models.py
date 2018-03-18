import datetime
import uuid
from pprint import pformat 
from peewee import *
from app import db, app
from playhouse.sqlite_ext import JSONField 
from playhouse.shortcuts import model_to_dict


class Conversation(db.Model):
    call_sid = CharField(max_length=100, primary_key=True, index=True)
    call_country = CharField(max_length=10, default='')
    call_zip = CharField(max_length=10, default='')
    call_state = CharField(max_length=10, index=True, default='')
    call_city = CharField(max_length=100, index=True, default='')
    call_number = CharField(max_length=20, default='')
    context = JSONField(null=True)
    history = JSONField(default={})
    last_update = DateTimeField(default=datetime.datetime.now)

    @classmethod
    def get_or_new(cls, form, call_sid=None):
        conv, created = Conversation.get_or_create(call_sid=call_sid)
        if created:
            app.logger.info('creating a new Conversation object')
            conv.call_country = form['CallerCountry']
            conv.call_zip = form['CallerZip']
            conv.call_state = form['CallerState']
            conv.call_city = form['CallerCity']
            conv.call_number = form['Caller']
            app.logger.info('copied over fields from the form')
        return conv, created

    def store_context(self):
        if 'context' not in self.history: self.history['context'] = []
        self.history['context'].append(self.context)

    def log_json(self):
        app.logger.info(pformat(model_to_dict(self)))

def create_tables():
    Conversation.create_table()

