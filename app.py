from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pprint import pprint
import logging

# flask-peewee bindings
from flask_peewee.db import Database
from playhouse.sqlite_ext import SqliteExtDatabase


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
cors = CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app)
app.config.from_object('config.Configuration')

db = SqliteExtDatabase('schedules.db')
logger = logging.getLogger('peewee')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
