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

		# Get DDB table from user-data
		userData = requests.get("http://169.254.169.254/latest/user-data")
		params = userData.json()
		
		# Get region from meta-data
		region = requests.get("http://169.254.169.254/latest/meta-data/placement/availability-zone")

                # Get table
                table = ddbcon.get_table(params["dnsCheckerDDB"])

                # Create item
                itemData = {
                        "response" : response
                }
                item = table.new_item(
                        hash_key=message["checkId"],
                        range_key=region.text[0:-1],
                        attrs=itemData
                )
                item.put()
                

        return ["moo"]

