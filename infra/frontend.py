from troposphere import Template, Ref, Tags, Output

from troposphere.iam import Role, InstanceProfile, PolicyType
from troposphere.sns import Topic
from troposphere.dynamodb import Table, AttributeDefinition, Key, ProvisionedThroughput
from troposphere.ec2 import *

from awacs.aws import Statement, Allow, Principal, Policy
from awacs.sts import AssumeRole

# Create the frontend stack and global resources

def create(AMIMap):
	# Create frontend Template
	frontend = Template()

	frontend.add_description("Stack defining the frontend for dnsChecker implementation including \
				global IAM resources, SNS Topic and DDB table")

	# Create AMI Map
	frontend.add_mapping("AMIMap",AMIMap)

	# Checker related IAM stuff lives in frontend stack since IAM is global 
	# and checker stacks will be run per region

	# Create checker IAM Role
	checkerRole = frontend.add_resource(
		Role(
			"checkerRole",
			AssumeRolePolicyDocument=Policy(
				Statement=[
					Statement(
						Effect=Allow,
						Action=[AssumeRole],
						Principal=Principal("Service",["ec2.amazonaws.com"])
					)
				]
			)
		)
	)

	# Create frontend IAM Role
	frontendRole = frontend.add_resource(
		Role(
			"frontendRole",
			AssumeRolePolicyDocument=Policy(
				Statement=[
					Statement(
						Effect=Allow,
						Action=[AssumeRole],
						Principal=Principal("Service",["ec2.amazonaws.com"])
					)
				]
			)
		)
	)


	# Create checker IAM Profile
	checkerProfile = frontend.add_resource(
		InstanceProfile(
			"checkerProfile",
			Roles=[Ref(checkerRole)],
		)
	)

	# Create frontend IAM Profile
	frontendProfile = frontend.add_resource(
		InstanceProfile(
			"frontendProfile",
			Roles=[Ref(frontendRole)],
		)
	)


	# Create IAM policy for checker instances
	checkerPolicy = frontend.add_resource(
		PolicyType(
			"checkerPolicy",
			PolicyName="checkerPolicy",
			# ToDo lock down actions and resources
			PolicyDocument={
				"Statement":[{
					"Effect": "Allow",
					"Action":[ 
						"sns:*",
						"dynamodb:*"
						],
					"Resource": "*"
				}]
			},
			Roles=[Ref(checkerRole)],
		)
	)

	# Create IAM policy for frontend instances
	frontendPolicy = frontend.add_resource(
		PolicyType(
			"frontendPolicy",
			PolicyName="frontendPolicy",
			# ToDo lock down actions and resources
			PolicyDocument={
				"Statement":[{
					"Effect": "Allow",
					"Action":[
						"sns:*",
						"dynamodb:*"
						],
					"Resource": "*"
				}]
			},
			Roles=[Ref(frontendRole)],
		)
	)


	# Create SNS topic
	checkerTopic = frontend.add_resource(
		Topic(
			"checkerTopic",
		)
	)

	
	# Create DDB Table
	dnsCheckerDDB = frontend.add_resource(
		Table(
			"dnsCheckerDDB",
			AttributeDefinitions=[
				AttributeDefinition(
					"checkId",
					"S"
				),
				AttributeDefinition(
					"region",
					"S"
				)
			],
			KeySchema=[
				Key(
					"checkId",
					"HASH"
				),
				Key(
					"region",
					"RANGE"
				)
			],
			ProvisionedThroughput=ProvisionedThroughput(
				1,
				1
			)
		)
	)

	# Create frontend VPC
	frontendVPC = frontend.add_resource(
		VPC(
			"frontendVPC",
			CidrBlock="10.0.0.0/16",
			Tags=Tags(
				Name="frontendVPC"
			)
		)
	)

	# Create frontend IGW
	frontendIGW = frontend.add_resource(
		InternetGateway(
			"frontendIGW"
		)
	)

	# Attach IGW to VPC
	frontendIGWAttachment = frontend.add_resource(
		VPCGatewayAttachment(
			"frontendIGWAttachment",
			VpcId=Ref(frontendVPC),
			InternetGatewayId=Ref(frontendIGW)
		)
	)

	# Create frontend Subnet
	frontendSubnet = frontend.add_resource(
		Subnet(
			"frontendSubnet",
			CidrBlock="10.0.0.0/24",
			VpcId=Ref(frontendVPC)
		)
	)

	# Create frontend RTB
	frontendRTB = frontend.add_resource(
		RouteTable(
			"frontendRTB",
			VpcId=Ref(frontendVPC)
		)
	)

	# Create route to IGW
	frontendDefaultRoute = frontend.add_resource(
		Route(
			"frontendDefaultRoute",
			DependsOn="frontendIGWAttachment",
			GatewayId=Ref(frontendIGW),
			DestinationCidrBlock="0.0.0.0/0",
			RouteTableId=Ref(frontendRTB)
		)
	)

	# Associate RTB with Subnet
	frontendSubnetRTBAssociation = frontend.add_resource(
		SubnetRouteTableAssociation(
			"frontendSubnetRTBAssociation",
			SubnetId=Ref(frontendSubnet),
			RouteTableId=Ref(frontendRTB)
		)
	)

	# Create frontend Security Group
	frontendSecurityGroup = frontend.add_resource(
		SecurityGroup(
			"frontendSecurityGroup",
			GroupDescription="Allow inbound access on port 80",
			SecurityGroupIngress=[
				SecurityGroupRule(
					IpProtocol="tcp",
					FromPort="80",
					ToPort="80",
					CidrIp="0.0.0.0/0"
				)
			],
			VpcId=Ref(frontendVPC)
		)
	)	
			
	# Create frontend Instance
	frontendInstance = frontend.add_resource(
		Instance(
			"frontendInstance",
			ImageId=FindInMap("AMIMap",Ref("AWS::Region"),"id"),
			InstanceType="t2.micro",
			KeyName="supportInstance",
			IamInstanceProfile=Ref(frontendProfile),
			NetworkInterfaces=[
				NetworkInterfaceProperty(
					GroupSet=[
						Ref(frontendSecurityGroup)
					],
					DeviceIndex="0",
					DeleteOnTermination="true",
					SubnetId=Ref(frontendSubnet),
					
				)
			],
			Tags=Tags(
				Name="frontendInstance"
			)
		)
	)

	# Create frontend EIP
	frontendEIP = frontend.add_resource(
		EIP(
			"frontendEIP",
			DependsOn="frontendIGWAttachment",
			Domain="vpc",
			InstanceId=Ref(frontendInstance)
		)
	)

	# Output SNS topic:
	frontend.add_output(
		[Output
			("snsTopic",
			Description="SNS Topic",
			Value=Ref(checkerTopic)
			)
		]
	)
	
	# Output Instance profile
	frontend.add_output(
		[Output
			("instanceProfile",
			Description="Instance Profile",
			Value=Ref(checkerProfile)
			)
		]
	)

        # Output DDB table
        frontend.add_output(
                [Output
                        ("dnsCheckerDDB",
                        Description="DynamoDB table",
                        Value=Ref(dnsCheckerDDB)
                        )
                ]
        )


	return frontend
