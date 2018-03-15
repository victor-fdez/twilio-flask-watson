from playhouse.sqlite_ext import SqliteExtDatabase

# config
class Configuration(object):
    DATABASE = {
        'name': 'schedules.db',
        'engine': 'playhouse.sqlite_ext.SqliteExtDatabase',
        'check_same_thread': False,
    }
    DEBUG = True
    SECRET_KEY = 'shhhh'

