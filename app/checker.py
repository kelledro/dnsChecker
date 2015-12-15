import requests
import json
import socket

def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/html")])
    data = json.loads(environ["wsgi.input"].read())
    # New subscription
    if environ["HTTP_X_AMZ_SNS_MESSAGE_TYPE"] == "SubscriptionConfirmation":
        request = requests.get(data["SubscribeURL"])
    # New notification
    elif environ["HTTP_X_AMZ_SNS_MESSAGE_TYPE"] == "Notification":
        message = json.loads(data["Message"])
        print socket.gethostbyname(message["hostname"])
    return ["moo"]

