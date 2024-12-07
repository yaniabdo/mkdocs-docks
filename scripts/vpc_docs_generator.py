#!/usr/binwq/env python3
import boto3
import markdown
import yaml
from datetime import datetime

def get_vpc_details(vpc, ec2):
    """Get detailed VPC information including subnets and route tables"""
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])['Subnets']
    route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])['RouteTables']
    
    subnet_info = []
    for subnet in subnets:
        name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
        subnet_info.append({
            'name': name,
            'cidr': subnet['CidrBlock'],
            'az': subnet['AvailabilityZone']
        })
    
    route_info = []
    for rt in route_tables:
        name = next((tag['Value'] for tag in rt.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
        routes = []
        for route in rt['Routes']:
            destination = route.get('DestinationCidrBlock', '')
            target = route.get('GatewayId', route.get('NatGatewayId', ''))
            routes.append({'destination': destination, 'target': target})
        route_info.append({'name': name, 'routes': routes})
    
    return subnet_info, route_info

def get_vpc_info(region):
    session = boto3.Session(region_name=region)
    ec2 = session.client('ec2')
    vpcs = ec2.describe_vpcs()
    
    vpc_info = []
    for vpc in vpcs['Vpcs']:
        name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
        environment = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Environment'), 'Unknown')
        
        subnets, route_tables = get_vpc_details(vpc, ec2)
        
        vpc_info.append({
            'name': name,
            'id': vpc['VpcId'],
            'cidr': vpc['CidrBlock'],
            'environment': environment,
            'region': region,
            'subnets': subnets,
            'route_tables': route_tables
        })
    return vpc_info

def generate_markdown(vpc_data):
    content = "# AWS VPC Configuration\n\n"
    content += f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for region, vpcs in vpc_data.items():
        content += f"## Region: {region}\n\n"
        
        for vpc in vpcs:
            content += f"### VPC: {vpc['name']}\n\n"
            content += f"* **VPC ID**: {vpc['id']}\n"
            content += f"* **CIDR Block**: {vpc['cidr']}\n"
            content += f"* **Environment**: {vpc['environment']}\n\n"
            
            content += "#### Subnets\n\n"
            content += "| Name | CIDR | Availability Zone |\n"
            content += "|------|------|------------------|\n"
            for subnet in vpc['subnets']:
                content += f"| {subnet['name']} | {subnet['cidr']} | {subnet['az']} |\n"
            content += "\n"
            
            content += "#### Route Tables\n\n"
            for rt in vpc['route_tables']:
                content += f"**{rt['name']}**\n\n"
                content += "| Destination | Target |\n"
                content += "|-------------|--------|\n"
                for route in rt['routes']:
                    content += f"| {route['destination']} | {route['target']} |\n"
                content += "\n"
    
    return content

def main():
    session = boto3.Session(region_name='us-west-1')  # Your AWS region
    regions = ['us-west-1']  # Add your regions
    vpc_data = {}
    
    for region in regions:
        vpc_data[region] = get_vpc_info(region)
    
    markdown_content = generate_markdown(vpc_data)
    
    # In main() function, update the file path
    with open('/home/ec2-user/mkdocs-vpc/docs/infrastructure/vpc-cloud.md', 'w') as f:
        f.write(markdown_content)

if __name__ == "__main__":
    main()
