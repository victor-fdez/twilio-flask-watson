from app import app, db

import api
from models import *


if __name__ == '__main__':
    create_tables()
    app.run()


