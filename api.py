from json import dumps
from flask import jsonify
from peewee import *
from app import db, app, socketio, emit
from playhouse.signals import post_save
from models import Appointment
from conversation_controller import process_voice_scheduling

@app.route('/voice/schedule/', methods=['GET', 'POST'])
def voice_schedule():
    return process_voice_scheduling()

@socketio.on('connect')
def handle_json():
    apps = Appointment.get_all_json()
    emit('events', apps)
    
@post_save(sender=Appointment)
def on_save_handler(model_class, instance, created):
    apps = Appointment.get_all_json()
    app.logger.info('new instance was just edited or saved')
    app.logger.info(apps)
    socketio.emit('events', apps, broadcast=True)

