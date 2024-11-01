from aws_cdk import (Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    CfnOutput,
    Duration,
    Tags)

import config as config
from constructs import Construct
from aws_cdk.aws_ecr_assets import Platform

PORT_NUMBER_CONTEXT = "PORT"

CONTAINER_ENV_NAME = "CONTAINER_ENV"

def get_port(env: dict) -> int:
    return int(env.get(PORT_NUMBER_CONTEXT))

class DockerFargateStack(Stack):

    def __init__(self, scope: Construct, context: str, env: dict, vpc: ec2.Vpc, **kwargs) -> None:
        stack_prefix = f'{env.get(config.STACK_NAME_PREFIX_CONTEXT)}'
        stack_id = f'{stack_prefix}-DockerFargateStack'
        super().__init__(scope, stack_id, **kwargs)

        #
        #============  Cluster ============
        #
        cluster = ecs.Cluster(
            self,
            f'{stack_id}-Cluster',
            vpc=vpc,
            container_insights=True
        )
        cluster.add_default_cloud_map_namespace(
        	name="local",
        	use_for_service_connect=True
        )
        
        #
        #============  First Service ===================
        #

        # Image
        proxy_image = ecs.ContainerImage.from_asset(
            directory=".",
            platform=Platform.LINUX_AMD64, # important to include when building locally, for testing
            build_args={"stack":context}
        )
        # Task
        proxy_task_image_options = ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                   image=proxy_image,
                   container_port = get_port(env))
        # Service
        load_balanced_fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            f'{stack_prefix}-Service-1',
            cluster=cluster,            # Required
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True), # Enable rollback on deployment failure
            task_image_options=proxy_task_image_options,
            public_load_balancer=True,  # Default is False
            protocol=elbv2.ApplicationProtocol.HTTP
        )

        #============  Second Service ===================
        
        container_name="my-apache-app"

        # Image and Task
        task_definition = ecs.FargateTaskDefinition(self, f'{stack_prefix}-TaskDef-2')
        task_definition.add_container("httpd",
          image=ecs.ContainerImage.from_registry("httpd:2.4"),
          port_mappings = [ecs.PortMapping(name=container_name, container_port=80)]
        )

        # Service
        second_service = ecs.FargateService(
            self,
            f'{stack_prefix}-Service-2',
            cluster=cluster,
            task_definition=task_definition,
            service_connect_configuration=ecs.ServiceConnectProps(
                services=[
                    ecs.ServiceConnectService(
                        port_mapping_name=container_name,
                        port=80,
                        dns_name=container_name
                    )
                ],
            )
        )

        # Tag all resources in this Stack's scope with context tags
        for key, value in env.get(config.TAGS_CONTEXT).items():
            Tags.of(scope).add(key, value)
