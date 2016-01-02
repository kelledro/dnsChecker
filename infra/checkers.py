from troposphere import Template, Ref, Tags, Join, Base64

from troposphere.ec2 import *

# Stack that creates a DNS checker instance

def create(AMIMap, instanceProfile, snsTopic, dnsCheckerDDB):
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
	# Create checker Instance Metadata
	checkerInstanceMetadata = {
		"AWS::CloudFormation::Init": {
			"config": {
				"packages": {
					"yum": {
						"docker": []
					}
				},
				"commands": {
					"makefolders": {
						"command" : "mkdir /var/www /var/log/nginx"
					},
					"getChecker.py": {
						"command": "get https://raw.githubusercontent.com/kelledro/dnsChecker/master/app/checker.py -O /var/www/checker.py"
					},
					"getChecker.ini": {
						"command": "wget https://raw.githubusercontent.com/kelledro/dnsChecker/master/app/checker.ini -O /var/www/checker.ini"
					},
					"runUwsgiContainer": {
						"command": "sudo docker run -dit --name uwsgi -v /var/www:/var/www kelledro/dnschecker_uwsgi"
					},
					"runNginx": {
						"command": "sudo docker run -dit --name nginx -v /var/log/nginx/:/var/log/nginx -v /var/www/:/var/www -p 80:80 dnschecker_nginx"
					}
				}
			}
		},
		"snsTopic" : snsTopic,
		"dnsCheckerDDB" : dnsCheckerDDB
	}

	# Create checker Instance
	checkerInstance = checker.add_resource(
		Instance(
			"checkerInstance",
			ImageId=FindInMap("AMIMap",Ref("AWS::Region"),"id"),
			InstanceType="t2.micro",
			KeyName="supportInstance", # TODO remove this after testing
			IamInstanceProfile=instanceProfile,
			Metadata=checkerInstanceMetadata,
			UserData=Base64(
				Join("",
					[
						"{ \"snsTopic\" : \"",
						snsTopic,
						"\",\n",
						"\"dnsCheckerDDB\" : \"",
						dnsCheckerDDB,
						"\"\n}"
					]
				)
			),
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

stack = create("foo","bar","moo","poo")
print stack.to_json()
