from __future__ import absolute_import, print_function

import json
from HTMLParser import HTMLParser

from geopy.geocoders import Nominatim

from gevent import monkey
monkey.patch_all()

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import time
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, join_room, leave_room, \
    close_room, disconnect

consumer_key="<INSERT KEY>"
consumer_secret="<INSERT KEY>"
access_token="<INSERT KEY>"
access_token_secret="<INSERT KEY>"

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None
geolocator = Nominatim()

def background_thread():
    """Example of how to send server generated events to clients."""
    """count = 0
    while True:
        time.sleep(10)
        count += 1
        socketio.emit('my response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')"""

def geocode_thread(status):
    status.text.encode('utf8')
    if status.coordinates:
	socketio.emit('coordinates',
	   {'lat': status.coordinates['coordinates'][1], 'long': status.coordinates['coordinates'][0], 'text': status.text},
		      namespace='/test')
    elif status.user.location:
	location = None
	try:
	    location = geolocator.geocode(status.user.location.encode('utf8'),timeout=5,exactly_one=True)
	except:
	    print ("Geocoding Error: " + unicode(status.user.location))
	    return
	if location is not None:
	    socketio.emit('coordinates',{'lat': location.latitude, 'long': location.longitude, 'text': status.text},namespace='/test')


@app.route('/')
def index():
    global thread
    if thread is None:
        thread = Thread(target=background_thread)
        thread.start()
    return render_template('index.html')


@socketio.on('my event', namespace='/test')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('my broadcast event', namespace='/test')
def test_broadcast_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         broadcast=True)


@socketio.on('join', namespace='/test')
def join(message):
    join_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('leave', namespace='/test')
def leave(message):
    leave_room(message['room'])
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'In rooms: ' + ', '.join(request.namespace.rooms),
          'count': session['receive_count']})


@socketio.on('close room', namespace='/test')
def close(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response', {'data': 'Room ' + message['room'] + ' is closing.',
                         'count': session['receive_count']},
         room=message['room'])
    close_room(message['room'])


@socketio.on('my room event', namespace='/test')
def send_room_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': message['data'], 'count': session['receive_count']},
         room=message['room'])


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my response',
         {'data': 'Disconnected!', 'count': session['receive_count']})
    disconnect()


@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my response', {'data': 'Connected', 'count': 0})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')

class MapListener(StreamListener):
    def on_status(self,status):
        thread = Thread(target=geocode_thread, args=(status,))
        thread.start()

    def on_error(self, status):
        print(status)

if __name__ == '__main__':
    l = MapListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)
    try:
        stream.filter(locations=[-180,-90,180,90],async=True)
        #stream.filter(track=["ISIS"],async=True)
    except:
        print ("Exception")
    socketio.run(app)


