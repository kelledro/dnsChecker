import boto.cloudformation
import boto.ec2
import fnmatch
import frontend
import checkers
import time
import sys
import json

# Main script that creates templates then creates CFN stacks

# Get latest AMIs
def getAMI():
	AMIMap = {}
	regions = boto.ec2.regions()
	for region in regions:
	        if not fnmatch.fnmatch(region.name,"cn-*") and not fnmatch.fnmatch(region.name,"*gov*"):
	                ec2conn = boto.ec2.connect_to_region(region.name)
	                images = ec2conn.get_all_images(owners=["amazon"], filters={"name": "amzn-ami-hvm-*.x86_64-gp2"})
	                latestDate = ""
	                latestAMI = ""
	                for image in images:
	                        if image.creationDate > latestDate:
	                                latestDate = image.creationDate
	                                latestAMI = image.id
                AMIMap[region.name] = {"id": latestAMI}
	return AMIMap

# create or update stack
def pushStack(conn,name,template):
	try:
		conn.create_stack(
			stack_name=name,
			template_body=template,
			capabilities=["CAPABILITY_IAM"]
		)
	except boto.exception.BotoServerError as e:
		error = json.loads(e.body)

		# Try updating if stack already exists
		if error["Error"]["Code"] == "AlreadyExistsException":
			print error["Error"]["Message"]
			try:
				conn.update_stack(
					stack_name=name,
					template_body=template,
					capabilities=["CAPABILITY_IAM"]
				)
			except boto.exception.BotoServerError as e:
				error = json.loads(e.body)

				# Print error eg: No updates
				if error["Error"]["Code"] == "ValidationError":
					print error["Error"]["Message"]

		# Print error eg: No updates
		elif error["Error"]["Code"] == "ValidationError":
			print error["Error"]["Message"]

# Disable dynamically getting AMIs to speed up testing
#AMIMap = getAMI()

AMIMap = { \
	'us-east-1': {'id': 'ami-60b6c60a'}, \
	'ap-northeast-1': {'id': 'ami-383c1956'}, \
	'sa-east-1': {'id': 'ami-6817af04'}, \
	'eu-central-1': {'id': 'ami-bc5b48d0'}, \
	'ap-southeast-1': {'id': 'ami-c9b572aa'}, \
	'ap-southeast-2': {'id': 'ami-48d38c2b'}, \
	'us-west-2': {'id': 'ami-f0091d91'}, 
	'us-gov-west-1': {'id': 'ami-f0091d91'}, \
	'us-west-1': {'id': 'ami-d5ea86b5'}, \
	'cn-north-1': {'id': 'ami-60b6c60a'}, \
	'eu-west-1': {'id': 'ami-bff32ccc'} \
}

# Create frontend stack template
frontendStack = frontend.create(AMIMap)

# Create or update frontend stack
print("Creating frontend stack in us-west-2")
cfnConnection = boto.cloudformation.connect_to_region("us-west-2")
pushStack(cfnConnection,"dnsCheckerFrontend",frontendStack.to_json()) 

# Wait for frontend stack to create so we can get the SNS topic and instance profile from it
print("Waiting for frontend stack creation")
cf = boto.cloudformation.connect_to_region("us-west-2")

stack = cf.describe_stacks("dnsCheckerFrontend")
print("."),
while stack[0].stack_status not in ("CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"):
	sys.stdout.flush()
        time.sleep(10)
	print("."),
        stack = cf.describe_stacks("dnsCheckerFrontend")     

print("\n")

for output in stack[0].outputs:
        if output.key == "instanceProfile":
                instanceProfile = output.value
        if output.key == "snsTopic":
                snsTopic = output.value
	if output.key == "dnsCheckerDDB":
		dnsCheckerDDB = output.value

# Create checker stack template
checkerStack = checkers.create(AMIMap, instanceProfile, snsTopic, dnsCheckerDDB)

# Create checker stacks
# Get list of regions
regions = boto.ec2.regions()
for region in regions:

	# Exclude China and gov cloud
	if not fnmatch.fnmatch(region.name,"cn-*") and not fnmatch.fnmatch(region.name,"*gov*"):
	
		# Launch checker stack in region
		print("Creating checker stack in %s" % region.name)
		cfnConnection = boto.cloudformation.connect_to_region(region.name)
		pushStack(cfnConnection,"dnsCheckerBackend",checkerStack.to_json())

print("Finished")
