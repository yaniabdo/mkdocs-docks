import boto3
import yaml
import os
from datetime import datetime

# Define base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config/aws_environments.yml')
OUTPUT_PATH = os.path.join(BASE_DIR, 'docs/infrastructure/vpc-cloud.md')

def load_config():
   """Load account configuration from YAML"""
   with open(CONFIG_PATH, 'r') as file:
       return yaml.safe_load(file)

def get_vpc_info(session, region):
   """Get VPC information for a specific region"""
   ec2 = session.client('ec2', region_name=region)
   vpcs = ec2.describe_vpcs()
   
   vpc_info = []
   for vpc in vpcs['Vpcs']:
       name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
       environment = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Environment'), 'Unknown')
       
       # Get subnets
       subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc['VpcId']]}])['Subnets']
       subnet_info = []
       for subnet in subnets:
           subnet_name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')
           subnet_info.append({
               'name': subnet_name,
               'cidr': subnet['CidrBlock'],
               'az': subnet['AvailabilityZone']
           })
       
       vpc_info.append({
           'name': name,
           'id': vpc['VpcId'],
           'cidr': vpc['CidrBlock'],
           'environment': environment,
           'subnets': subnet_info
       })
   
   return vpc_info

def generate_markdown(accounts_data):
    """Generate markdown documentation with enhanced styling"""
    content = """# AWS VPC Configuration

!!! info "Last Updated"
    **{timestamp}**

""".format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    for account in accounts_data:
        content += f"""## Project: {account['name']}

!!! abstract "Infrastructure Overview"
    Network architecture for {account['name']} project
        
"""
        for env in account['environments']:
            content += f"""### Environment: {env}

!!! example "Network Details"

"""
            if 'vpcs' in account and env in account['vpcs']:
                # Add Mermaid diagram for VPC structure
                content += "```mermaid\ngraph TB\n"
                for region, vpcs in account['vpcs'][env].items():
                    for vpc in vpcs:
                        content += f"    {vpc['id']}[{vpc['name']}<br/>{vpc['cidr']}]\n"
                        for subnet in vpc['subnets']:
                            subnet_id = subnet['name'].replace('-', '_')
                            content += f"    {vpc['id']} --> {subnet_id}[{subnet['name']}<br/>{subnet['cidr']}]\n"
                content += "```\n\n"

                for region, vpcs in account['vpcs'][env].items():
                    for vpc in vpcs:
                        content += f"""#### VPC: {vpc['name']} ({region})

!!! info "VPC Details"
    - **VPC ID**: `{vpc['id']}`
    - **CIDR Block**: `{vpc['cidr']}`

"""
                        if vpc['subnets']:
                            content += "##### Subnets\n\n"
                            content += """| Name | CIDR | Availability Zone |
|:-----|:-----|:-----------------|
"""
                            for subnet in vpc['subnets']:
                                content += f"| `{subnet['name']}` | `{subnet['cidr']}` | `{subnet['az']}` |\n"
                            content += "\n"
            else:
                content += "No VPCs found for this environment\n\n"
    
    return content

def main():
   config = load_config()
   regions = ['us-east-1', 'us-east-2']  # Add your regions
   
   for account in config['accounts']:
       account['vpcs'] = {}
       
       try:
           session = boto3.Session()  # Uses EC2 instance role
           
           for env in account['environments']:
               account['vpcs'][env] = {}
               for region in regions:
                   vpcs = get_vpc_info(session, region)
                   # Filter VPCs by environment tag
                   env_vpcs = [vpc for vpc in vpcs if vpc['environment'].lower() == env.lower()]
                   if env_vpcs:
                       account['vpcs'][env][region] = env_vpcs
       
       except Exception as e:
           print(f"Error processing account {account['name']}: {str(e)}")
   
   markdown_content = generate_markdown(config['accounts'])
   
   with open(OUTPUT_PATH, 'w') as f:
       f.write(markdown_content)

if __name__ == "__main__":
   main()
