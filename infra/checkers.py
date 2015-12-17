from troposphere import Template, Ref, Tags

from troposphere.ec2 import *

# Stack that creates a DNS checker instance

def create(AMIMap, instanceProfile, snsTopic):
	# Create checker stack
	checker = Template()

	checker.add_description("Stack defining the checker instance for dnsChecker implementation")

	# Create AMI Map
	checker.add_mapping("AMIMap",AMIMap)

	# Create checker VPC
	checkerVPC = checker.add_resource(
		VPC(
			"checkerVPC",
			CidrBlock="10.0.0.0/16",
			Tags=Tags(
				Name="checkerVPC"
			)
		)
	)

	# Create checker IGW
	checkerIGW = checker.add_resource(
		InternetGateway(
			"checkerIGW"
		)
	)

	# Attach IGW to VPC
	checkerIGWAttachment = checker.add_resource(
		VPCGatewayAttachment(
			"checkerIGWAttachment",
			VpcId=Ref(checkerVPC),
			InternetGatewayId=Ref(checkerIGW)
		)
	)

	# Create checker Subnet
	checkerSubnet = checker.add_resource(
		Subnet(
			"checkerSubnet",
			CidrBlock="10.0.0.0/24",
			VpcId=Ref(checkerVPC)
		)
	)

	# Create checker RTB
	checkerRTB = checker.add_resource(
		RouteTable(
			"checkerRTB",
			VpcId=Ref(checkerVPC)
		)
	)

	# Create route to IGW
	checkerDefaultRoute = checker.add_resource(
		Route(
			"checkerDefaultRoute",
			DependsOn="checkerIGWAttachment",
			GatewayId=Ref(checkerIGW),
			DestinationCidrBlock="0.0.0.0/0",
			RouteTableId=Ref(checkerRTB)
		)
	)

	# Associate RTB with Subnet
	checkerSubnetRTBAssociation = checker.add_resource(
		SubnetRouteTableAssociation(
			"checkerSubnetRTBAssociation",
			SubnetId=Ref(checkerSubnet),
			RouteTableId=Ref(checkerRTB)
		)
	)

	# Create checker Security Group

	checkerSecurityGroup = checker.add_resource(
		SecurityGroup(
			"checkerSecurityGroup",
			GroupDescription="Allow inbound access on port 80",
			SecurityGroupIngress=[
				SecurityGroupRule(
					IpProtocol="tcp",
					FromPort="80",
					ToPort="80",
					CidrIp="0.0.0.0/0"
				)
			],
			VpcId=Ref(checkerVPC)
		)
	)

	# Create checker Instance
	checkerInstance = checker.add_resource(
		Instance(
			"checkerInstance",
			ImageId=FindInMap("AMIMap",Ref("AWS::Region"),"id"),
			InstanceType="t2.micro",
			KeyName="supportInstance",
			IamInstanceProfile=instanceProfile,
			# need to pass checkerProfile from frontend stack
			#IamInstanceProfile=Ref(checkerProfile),
			NetworkInterfaces=[
				NetworkInterfaceProperty(
					GroupSet=[
						Ref(checkerSecurityGroup)
					],
					AssociatePublicIpAddress="true",
					DeviceIndex="0",
					DeleteOnTermination="true",
					SubnetId=Ref(checkerSubnet),

				)
			],
			Tags=Tags(
				Name="checkerInstance"
			)
		)
	)
	return checker
