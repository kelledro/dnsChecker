import boto.dynamodb
import requests
import json
import socket

def application(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/html")])
        data = json.loads(environ["wsgi.input"].read())

        # New subscription
        if environ["HTTP_X_AMZ_SNS_MESSAGE_TYPE"] == "SubscriptionConfirmation":

                # Respond to subscription by hitting the SubscribeURL
                request = requests.get(data["SubscribeURL"])

        # New notification
        elif environ["HTTP_X_AMZ_SNS_MESSAGE_TYPE"] == "Notification":

                # Load data from SNS notification
                message = json.loads(data["Message"])

                # Do DNS lookup
                response = socket.gethostbyname(message["hostname"])

                # Connect to DDB
                ddbcon = boto.dynamodb.connect_to_region("us-west-2")

                # Read configuration from conf file
                confFile = open("/tmp/checker.conf","r")
                conf = json.loads(confFile.read())

                # Get table
                table = ddbcon.get_table(conf["dnsCheckerDDB"])

                # Create item
                itemData = {
			"hostname" : message["hostname"],
                        "response" : response
                }
                item = table.new_item(
                        hash_key=message["checkId"],
                        range_key=conf["region"],
                        attrs=itemData
                )
                item.put()


        return ["moo"]
