import datetime
import uuid
from pprint import pformat, pprint
from peewee import *
from app import db, app
from playhouse.signals import Model
from playhouse.sqlite_ext import JSONField 
from playhouse.shortcuts import model_to_dict


class Business(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=20, default='')
    phone = CharField(max_length=20, null=False, index=True)

    class Meta:
        database = db
    
    @classmethod
    def get_using_form(cls, form):
        caller = form['To']
        if caller:
            business = cls.get_or_none(cls.phone == caller)
            return business
        return None

class Customer(Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    name = CharField(max_length=30, default='')
    phone = CharField(max_length=20, default='', index=True)
    business = ForeignKeyField(Business, backref='customer')

    class Meta:
        database = db

    @classmethod
    def get_using_form(cls, form, business=None):
        caller = form['From']
        if caller:
            customer = cls.get_or_none((cls.phone == caller) & (cls.business == business))
            return customer 
        return None


class Appointment(Model):
    customer = ForeignKeyField(Customer, backref='appointment')
    note = CharField(max_length=200, default='')
    start = DateTimeField(null=False, index=True)
    end = DateTimeField(null=False, index=True)

    class Meta:
        database = db

    @classmethod
    def get_all_json(cls):
        apps = Appointment.select()
        clean_dicts = [{ 
            'id': idx,
            'title': f"{app.customer.name} - {app.customer.business.name}",
            'name': app.customer.name,
            'phone': app.customer.phone,
            'business': app.customer.business.name,
            'start': app.start.strftime('%Y-%m-%dT%H:%M:%S'),
            'end': app.end.strftime('%Y-%m-%dT%H:%M:%S')
        } for idx, app in enumerate(apps) ]
        return clean_dicts


class Conversation(Model):
    business = ForeignKeyField(Business, backref='conversation')
    customer = ForeignKeyField(Customer, null=True, backref='conversation')
    call_sid = CharField(max_length=100, primary_key=True, index=True)
    call_country = CharField(max_length=10, default='')
    call_zip = CharField(max_length=10, default='')
    call_state = CharField(max_length=10, index=True, default='')
    call_city = CharField(max_length=100, index=True, default='')
    call_number = CharField(max_length=20, default='')
    context = JSONField(null=True)
    history = JSONField(default={})
    last_update = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db  

    @classmethod
    def get_or_new(cls, form, call_sid=None):
        conv = Conversation.get_or_none(call_sid=call_sid)
        if conv:
            return conv, False, ""
        buss = Business.get_using_form(form)
        cust = Customer.get_using_form(form, business=buss)
        context = {'conversation_id': '', 'system': {}}
        if buss:
            context['business'] = buss.name
            if cust:
                context['name'] = cust.name
                context['identified'] = 'true'
            else:
                context['identified'] = 'false'
            conv = Conversation.create(
                call_sid=call_sid,
                call_country=form['CallerCountry'],
                call_zip=form['CallerZip'],
                call_state=form['CallerState'],
                call_city=form['CallerCity'],
                call_number=form['Caller'],
                business=buss,
                customer=cust,
                context=context
            )
            return conv, True, ""
        else:
            return None, False, "Line is not setup to accept call for any business."

    def identity_affirmed(self):
        return (
            self.context and
            ('identified' in self.context and self.context['identified'] == 'true') and
            ('identity_affirmed' in self.context and self.context['identity_affirmed'] == 'true')
        )

    def store_context(self):
        if 'context' not in self.history: self.history['context'] = []
        self.history['context'].append(self.context)

    def log_json(self):
        app.logger.info(pformat(model_to_dict(self)))

def create_tables():
    db.create_tables([Business, Customer, Appointment, Conversation])
    business = Business.create(name="Math Tutoring Inc.", phone="+19158000459") 
    #customer = Customer.create(name="Victor", phone="+19154710552", business=business) 
    #customer.save()

@app.cli.command()
def initdb():
    """Initialize the database."""
    print("Create DB and tables") 
    create_tables()
