import json
import boto3
import traceback

ec2 = boto3.client('ec2')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VpcInfoTable')

def lambda_handler(event, context):
    try:
        method = event.get('httpMethod', '')
        if method == 'POST':
            body = json.loads(event.get('body', '{}'))
            vpc_name = body.get('vpcName')
            if not vpc_name:
                return { 'statusCode': 400, 'body': json.dumps({'error': 'Missing vpcName'}) }

            # Define subnet CIDR blocks
            subnet_cidrs = ['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24']  # Example CIDR blocks

            # Check if VPC already exists by name
            vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [vpc_name]}])['Vpcs']
            if vpcs:
                vpc = vpcs[0]
                vpc_id = vpc['VpcId']
                vpc_exists = True
                message = 'VPC already exists. Creating subnets for existing VPC.'
            else:
                # Create new VPC if not found
                vpc = ec2.create_vpc(CidrBlock='10.0.0.0/16')
                vpc_id = vpc['Vpc']['VpcId']
                ec2.create_tags(Resources=[vpc_id], Tags=[{'Key': 'Name', 'Value': vpc_name}])
                message = 'New VPC created.'

            # Create an Internet Gateway if not attached
            igw_response = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])
            if not igw_response['InternetGateways']:
                igw = ec2.create_internet_gateway()['InternetGateway']['InternetGatewayId']
                ec2.attach_internet_gateway(InternetGatewayId=igw, VpcId=vpc_id)
            else:
                igw = igw_response['InternetGateways'][0]['InternetGatewayId']

            # Create the subnets
            subnet_ids = []
            for cidr in subnet_cidrs:
                # Check if subnet exists with the same CIDR block
                subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
                existing_subnet = next((subnet for subnet in subnets if subnet['CidrBlock'] == cidr), None)
                if existing_subnet:
                    subnet = existing_subnet
                    subnet_id = subnet['SubnetId']
                    subnet_exists = True
                    message += f' Subnet with CIDR {cidr} already exists.'
                else:
                    # Create new subnet if not found
                    subnet = ec2.create_subnet(VpcId=vpc_id, CidrBlock=cidr)
                    subnet_id = subnet['Subnet']['SubnetId']
                    subnet_exists = False
                    message += f' New subnet created with CIDR {cidr}.'
                subnet_ids.append(subnet_id)

            # Create a route table and associate it with each subnet
            route_table_response = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
            route_table = next((rt for rt in route_table_response if 'Routes' in rt and any(route.get('GatewayId') == igw for route in rt['Routes'])), None)
            if not route_table:
                route_table = ec2.create_route_table(VpcId=vpc_id)['RouteTable']
                route_table_id = route_table['RouteTableId']
                ec2.create_route(RouteTableId=route_table_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw)
                for subnet_id in subnet_ids:
                    ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)
            else:
                route_table_id = route_table['RouteTableId']
                for subnet_id in subnet_ids:
                    ec2.associate_route_table(RouteTableId=route_table_id, SubnetId=subnet_id)

            # Add entry to DynamoDB whether VPC exists or was newly created
            table.put_item(Item={
                'VpcId': vpc_id,
                'VpcName': vpc_name,
                'InternetGatewayId': igw,
                'SubnetIds': subnet_ids,
                'RouteTableId': route_table_id
            })

            return { 
                'statusCode': 200, 
                'body': json.dumps({
                    'VpcId': vpc_id, 
                    'SubnetIds': subnet_ids, 
                    'InternetGatewayId': igw, 
                    'RouteTableId': route_table_id,
                }) 
            }

        elif method == 'GET':
            result = table.scan()
            return { 'statusCode': 200, 'body': json.dumps(result.get('Items', [])) }
        else:
            return { 'statusCode': 405, 'body': json.dumps({'error': 'Method not allowed'}) }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e), 'trace': traceback.format_exc()})
        }
