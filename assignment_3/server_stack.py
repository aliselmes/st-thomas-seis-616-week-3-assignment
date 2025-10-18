import os.path

from aws_cdk.aws_s3_assets import Asset as S3asset

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_rds as rds,
    CfnOutput,
    RemovalPolicy,
    Duration,
)

from constructs import Construct

dirname = os.path.dirname(__file__)

class ServerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, 
                 vpc: ec2.Vpc, 
                 web_server_sg: ec2.SecurityGroup,
                 rds_sg: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Instance Role and SSM Managed Policy
        instance_role = iam.Role(
            self, "InstanceSSM",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        instance_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )
        
        # Get public subnets (one in each AZ)
        public_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets
        
        # Script in S3 as Asset - upload script into s3 bucket
        web_init_script_asset = S3asset(
            self, "Asset",
            path=os.path.join(dirname, "configure.sh")
        )
        
        # Create web server 1 in first public subnet
        web_server_1 = ec2.Instance(
            self, "WebServer1",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            vpc_subnets=ec2.SubnetSelection(subnets=[public_subnets[0]]),
            security_group=web_server_sg,
            role=instance_role
        )
        
        # Userdata executes script from S3 for web server 1
        asset_path_1 = web_server_1.user_data.add_s3_download_command(
            bucket=web_init_script_asset.bucket,
            bucket_key=web_init_script_asset.s3_object_key
        )
        web_server_1.user_data.add_execute_file_command(file_path=asset_path_1)
        web_init_script_asset.grant_read(web_server_1.role)
        
        # Allow inbound HTTP traffic in security groups for web server 1
        web_server_1.connections.allow_from_any_ipv4(ec2.Port.tcp(80))
        
        # Create web server 2 in second public subnet
        web_server_2 = ec2.Instance(
            self, "WebServer2",
            vpc=vpc,
            instance_type=ec2.InstanceType("t2.micro"),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            vpc_subnets=ec2.SubnetSelection(subnets=[public_subnets[1]]),
            security_group=web_server_sg,
            role=instance_role
        )
        
        # Userdata executes script from S3 for web server 2
        asset_path_2 = web_server_2.user_data.add_s3_download_command(
            bucket=web_init_script_asset.bucket,
            bucket_key=web_init_script_asset.s3_object_key
        )
        web_server_2.user_data.add_execute_file_command(file_path=asset_path_2)
        web_init_script_asset.grant_read(web_server_2.role)
        
        # Allow inbound HTTP traffic in security groups for web server 2
        web_server_2.connections.allow_from_any_ipv4(ec2.Port.tcp(80))
        
        # Create RDS subnet group with all private subnets
        db_subnet_group = rds.SubnetGroup(
            self, "DBSubnetGroup",
            description="Subnet group for RDS instance",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create RDS MySQL instance with minimum configuration
        db_instance = rds.DatabaseInstance(
            self, "MySQLInstance",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            subnet_group=db_subnet_group,
            security_groups=[rds_sg],
            multi_az=False,
            allocated_storage=20,
            max_allocated_storage=20,
            database_name="mydatabase",
            backup_retention=Duration.days(0),
            delete_automated_backups=True,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
            publicly_accessible=False
        )
        
        # Outputs
        CfnOutput(
            self, "WebServer1PublicIp",
            value=web_server_1.instance_public_ip,
            description="Web Server 1 Public IP"
        )
        
        CfnOutput(
            self, "WebServer2PublicIp",
            value=web_server_2.instance_public_ip,
            description="Web Server 2 Public IP"
        )
        
        CfnOutput(
            self, "RDSEndpoint",
            value=db_instance.db_instance_endpoint_address,
            description="RDS Instance Endpoint"
        )