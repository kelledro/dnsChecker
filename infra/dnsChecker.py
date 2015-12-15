import boto.cloudformation
import boto.ec2
import fnmatch
import frontend
import checkers

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

AMIMap = getAMI()

# Create frontend stack template
frontendStack = frontend.create(AMIMap)

# Create checker stack template
checkerStack = checkers.create(AMIMap)

# Create or update frontend stack
cfnConnection = boto.cloudformation.connect_to_region("us-west-2")
cfnConnection.create_stack(
        stack_name="dnsCheckerFrontend", 
        template_body=frontendStack.to_json(), 
        capabilities=["CAPABILITY_IAM"]
)
# Create checker stacks
# Get list of regions
regions = boto.ec2.regions()
for region in regions:

	# Exclude China and gov cloud
	if not fnmatch.fnmatch(region.name,"cn-*") and not fnmatch.fnmatch(region.name,"*gov*"):
	
		# Launch checker stack in region
		cfnConn = boto.cloudformation.connect_to_region(region.name)
		cfnConn.create_stack(
			stack_name="dnsCheckerChecker",
			template_body=checkerStack.to_json()
		)
