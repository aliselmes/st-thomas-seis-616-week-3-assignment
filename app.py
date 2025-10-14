#!/usr/bin/env python3
import aws_cdk as cdk
from assignment_3.network_stack import NetworkStack
from assignment_3.server_stack import ServerStack

app = cdk.App()

# Create network stack
network_stack = NetworkStack(app, "NetworkStack")

# Create server stack that depends on network stack
server_stack = ServerStack(
    app, "ServerStack",
    vpc=network_stack.vpc,
    web_server_sg=network_stack.web_server_sg,
    rds_sg=network_stack.rds_sg
)

# Add dependency
server_stack.add_dependency(network_stack)

app.synth()