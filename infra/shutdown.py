import boto.cloudformation
import boto.ec2
import fnmatch
import time
import sys

regions = boto.ec2.regions()
for region in regions:

	# Exclude China and gov cloud
	if not fnmatch.fnmatch(region.name,"cn-*") and not fnmatch.fnmatch(region.name,"*gov*"):

		# Launch checker stack in region
		print("Deleting dnsChecker stack(s) in %s" % region.name)
		cfnConnection = boto.cloudformation.connect_to_region(region.name)
		stacks = cfnConnection.describe_stacks()
		for stack in stacks:
			if fnmatch.fnmatch(stack.stack_name,"dnsChecker*"):
				print "deleting %s" % stack.stack_id
				cfnConnection.delete_stack(stack.stack_name)
