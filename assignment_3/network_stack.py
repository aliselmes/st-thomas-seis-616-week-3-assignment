from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput,
)
from constructs import Construct

class NetworkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create a VPC with 2 AZs, with 1 public and 1 private subnet in each AZ
        self.vpc = ec2.Vpc(
            self, "AssignmentVPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )
        
        # Create security group for web servers
        self.web_server_sg = ec2.SecurityGroup(
            self, "WebServerSecurityGroup",
            vpc=self.vpc,
            description="Security group for web servers",
            allow_all_outbound=True
        )
        
        # Allow HTTP traffic from anywhere on port 80
        self.web_server_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP from anywhere"
        )
        
        # Create security group for RDS
        self.rds_sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=self.vpc,
            description="Security group for RDS instance",
            allow_all_outbound=True
        )
        
        # Allow MySQL traffic only from web servers
        self.rds_sg.add_ingress_rule(
            self.web_server_sg,
            ec2.Port.tcp(3306),
            "Allow MySQL from web servers only"
        )
        
        # Outputs
        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID"
        )