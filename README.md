# dnsChecker
Mimic https://cachecheck.opendns.com/ using boto to spin up CloudFormation via troposphere.

## Infrastructure
This set of python scripts uses the troposphere library to create the JSON required by CloudFormation. Boto is then used to call CloudFormation and create stacks from the troposphere JSON. It creates a frontend stack which contains the web interface, SNS topic, DynamoDB table and required IAM resources. It then loops through all usable regions creating a checker stack in each.

## Work flow
The web interface will allow the user to provide a hostname to check. This will be published to the SNS topic that all the checker instances in each region are subscribed. The checker instances are listening on an HTTP endpoint for the SNS notification and will perform the DNS resolution as requested. They will then add their results to the DynamoDB table. The front end polls the DynamoDB table and displays the results as they become available.
