from app import app, socketio 

import api

if __name__ == '__main__':
    socketio.run(app)
