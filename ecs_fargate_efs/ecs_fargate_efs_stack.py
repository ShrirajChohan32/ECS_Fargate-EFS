from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_secretsmanager as aws_secrets_manager,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_efs as efs,
    aws_ecs_patterns as ecs_patterns,
)
from constructs import Construct

from aws_cdk import aws_logs as logs
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_s3 as s3
import aws_cdk as cdk

from aws_cdk.aws_ecs import (
    FargateTaskDefinition,
    MountPoint,
    Volume,
    DockerVolumeConfiguration,
)


class EcsFargateEfsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

   # Define a VPC
        vpcID ="vpc-08e1e0b3cf9b6c4cd"
        vpc = ec2.Vpc.from_lookup(self,"vpc",vpc_id=vpcID)


        # Create a Task Execution Role
        policy_doc = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "logs:CreateLogStream",
                        "elasticfilesystem:*",
                        "ec2:Describe*",
                        "cloudwatch:*",
                        "logs:PutLogEvents"
                    ],
                    resources=["*"]
                )
            ]
        )

        custom_role = iam.Role(
            self, "ecs_task_execution_role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "MyPolicy": policy_doc
            }
        )

        # create a security group for the EFS mount targets
        efs_security_group = ec2.SecurityGroup(self, "EFSSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="EFS Mount Target Security Group"
        )
        efs_security_group.add_ingress_rule(ec2.Peer.ipv4("0.0.0.0/0"), 
            ec2.Port.tcp(2049), "Allow NFS traffic from anywhere")

    # Create an EFS file system
        efs_file_system = efs.FileSystem(self, "MyEfsFileSystem",
            vpc=vpc,
            security_group=efs_security_group,
            encrypted=True,
            removal_policy=cdk.RemovalPolicy.DESTROY # Set the removal policy as per your requirements
        )

        # Create a container image from a Dockerfile in a directory
        asset = ecs.ContainerImage.from_asset(
            directory="./", file="Dockerfile.yml"
        )

        # Create a Cluster
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)

        # Define your Fargate task definition
        task_definition = ecs.FargateTaskDefinition(
            self, "MyTaskDefinition",
            execution_role=custom_role,
            cpu=2048,
            memory_limit_mib=8192
        )
        container = task_definition.add_container(
            "MyContainer",
            image=asset,
            memory_limit_mib=512,
            cpu=512,
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="my-container",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            command=[
                "/bin/bash",
                "-c",
                "while true; do echo 'Hello, World!'; sleep 10; done"
                ] 
            )

    # Create a volume in your Task Definition using the EFS mount target
        task_definition.add_volume(
            name="efs-volume",
            efs_volume_configuration=ecs.EfsVolumeConfiguration(
                file_system_id=efs_file_system.file_system_id,
                root_directory="/",
                transit_encryption="ENABLED",
            ),
        )

    # Attach the volume to your container
        container.add_mount_points(
            ecs.MountPoint(
                container_path="/home/kasm-user",
                source_volume="efs-volume",
                read_only=False,
            )
        )
        

        # Create a Fargate service using the task definition
        service = ecs.FargateService(
            self, "MyService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=3,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            assign_public_ip=True
            )
        
        container.add_port_mappings(
            ecs.PortMapping(container_port=3000),
        )

        service.connections.allow_from_any_ipv4(ec2.Port.tcp(3000))
        service.connections.allow_from_any_ipv4(ec2.Port.tcp(2049))