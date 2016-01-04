from troposphere import Template, Ref, Tags, Join, Base64, GetAtt

from troposphere.ec2 import *
from troposphere.autoscaling import Metadata
from troposphere.cloudformation import *

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

	# Create checker instance metadata
	checkerInstanceMetadata = Metadata(
		Init(
			# Use ConfigSets to ensure docker service is running before trying to run containers
			# (since cfn-init runs "services" block last)
			InitConfigSets(
				ordered=["first","second"]
			),
			first=InitConfig(
				packages={
					"yum": {
						"docker": [],
						"curl": []
					}
				},
				files=InitFiles(
					{
						"/etc/cfn/cfn-hup.conf": InitFile(
							content=Join("",
								[
									"[main]\n",
									"stack=",Ref("AWS::StackName"),"\n",
									"region=",Ref("AWS::Region"),"\n"
								]
							),
							mode="000400",
							owner="root",
							group="root"
						),
						"/etc/cfn/hooks.d/cfn-auto-reloader.conf": InitFile(
							content=Join("",
								[
									"[cfn-auto-reloader-hook]\n",
									"triggers=post.update\n",
									"path=Resources.checkerInstance.Metadata\n",
									"action=/opt/aws/bin/cfn-init -v --stack ", Ref("AWS::StackName"), " ",
									"--resource checkerInstance ",
									"--region ", Ref("AWS::Region"), " ",
									"-c ordered\n",
									"runas=root\n"
								]
							),
							mode="000400",
							owner="root",
							group="root"
						),
						"/tmp/checker.conf": InitFile(
							content=Join("",
								[
									"{\n",
									"\"dnsCheckerDDB\" : \""+dnsCheckerDDB+"\",\n",
									"\"region\" : \"", Ref("AWS::Region"), "\"\n",
									"}"
								]
							),
							mode="000400",
							owner="root",
							group="root"
						)
					}
				),
				services={
					"sysvinit": InitServices(
						{
							"docker": InitService(
								enabled=True,
								ensureRunning=True
							),
							"cfn-hup": InitService(
								enabled=True,
								ensureRunning=True,
								files=[
									"/etc/cfn/cfn-hup.conf",
									"/etc/cfn/hooks.d/cfn-auto-reloader.conf"
								]
							)
						}
					)
				}
			),
			second=InitConfig(
				commands={
					"02runNginxContainer": {
						"command" : Join("",
							[
								"docker run -dit --name nginx -v /var/log/nginx/:/var/log/nginx ",
								"-v /tmp/:/tmp -p 80:80 kelledro/dnschecker_nginx"
							]
						)
					},
					"01runUwsgiContainer": {
						"command" : "docker run -dit --name uwsgi -v /tmp:/tmp kelledro/dnschecker_uwsgi"
					},
					"50subscribeToSNS": {
						"command": Join("",
							[
								"aws sns subscribe --protocol http --topic-arn ", snsTopic, " ",
								"--notification-endpoint http://$(curl -s 169.254.169.254/latest/meta-data/public-ipv4) ",
								"--region ", Ref("AWS::Region")
							]
						)
					}
				}
			)
		)
	)

	# Create checker Instance
	checkerInstance = checker.add_resource(
		Instance(
			"checkerInstance",
			ImageId=FindInMap("AMIMap",Ref("AWS::Region"),"id"),
			InstanceType="t2.micro",
			KeyName="kelledy", # TODO remove this after testing
			IamInstanceProfile=instanceProfile,
			Metadata=checkerInstanceMetadata,
			UserData=Base64(
				Join("",
					[
						"#!/bin/bash\n",
						"/opt/aws/bin/cfn-init -v ",
						"--stack ", Ref("AWS::StackName"), " ",
						"--resource checkerInstance ",
						"--region ", Ref("AWS::Region"), " ",
						"-c ordered"
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
