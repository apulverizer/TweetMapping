# -*- coding: UTF-8 -*-
from __future__ import absolute_import, print_function
from gevent import monkey # background threads
monkey.patch_all()
# import tweepy twitter stuff
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from threading import Thread
# import flask stuff
from flask import Flask, render_template
from flask_socketio import SocketIO

# From Twitter Developer Account
consumer_key = "<Consumer key>"
consumer_secret = "<Consumer secret>"
access_token = "<Access Token>"
access_token_secret = "<Access Token Secret>"

# Flask Stuff
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None


def tweet_handler(status):
    """
    This sends part of the tweet via websocket to the website
    This could be modified to store tweets in a db or file
    :param status: (string) The tweet to process
    :return:
    """
    status.text.encode('utf8')
    # if the status has coordinates
    if status.coordinates:
        # Send some json to the website
        socketio.emit('coordinates',
                      {'lat': status.coordinates['coordinates'][1], 'long': status.coordinates['coordinates'][0],
                       'text': status.text},
                      namespace='/test')
        print(status.text)


@app.route('/')
def index():
    """
    Flask route for root of website
    :return:
    """
    # render the index.html template
    return render_template('index.html')


class MapListener(StreamListener):
    """
    Background thread to process tweets
    """

    def on_status(self, status):
        # When we get a new status, process it in the background
        thread = Thread(target=tweet_handler, args=(status,))
        thread.start()

    def on_error(self, status):
        print(status)


if __name__ == '__main__':
    l = MapListener()  # The background listener
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)
    try:
        # Only get tweets with location
        stream.filter(locations=[-180, -90, 180, 90], async=True)
    except:
        # if the stream isns't going or something
        print("Exception")
    # run the webserver
    socketio.run(app)