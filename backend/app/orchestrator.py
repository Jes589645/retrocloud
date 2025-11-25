import os
import time
from typing import Optional, Dict, Any

import boto3


class GameOrchestrator:
    """
    Pequeño orquestador para crear VMs de juego en EC2 usando una AMI específica.
    """

    def __init__(
        self,
        ami_id: str,
        region_name: str = "us-east-2",
        instance_type: str = "m7i-flex.large",
    ) -> None:
        if not ami_id:
            raise ValueError("GAME_AMI_ID no está configurado en el entorno")

        self.ami_id = ami_id
        self.region_name = region_name
        self.instance_type = instance_type

        # La sesión usará tus credenciales configuradas con `aws configure`
        self.session = boto3.Session(region_name=self.region_name)
        self.ec2_resource = self.session.resource("ec2")

    def _build_run_instances_params(self, user_id: int, game_id: int) -> Dict[str, Any]:
        """
        Construye el diccionario de parámetros para ec2.create_instances()
        leyendo datos de variables de entorno.
        """
        params: Dict[str, Any] = {
            "ImageId": self.ami_id,
            "InstanceType": self.instance_type,
            "MinCount": 1,
            "MaxCount": 1,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": "Project", "Value": "retrocloud"},
                        {"Key": "GameId", "Value": str(game_id)},
                        {"Key": "UserId", "Value": str(user_id)},
                    ],
                }
            ],
        }

        key_name = os.getenv("GAME_KEYPAIR_NAME")
        if key_name:
            params["KeyName"] = key_name

        sg_ids = os.getenv("GAME_SG_IDS")
        if sg_ids:
            params["SecurityGroupIds"] = [s.strip() for s in sg_ids.split(",") if s.strip()]

        subnet_id = os.getenv("GAME_SUBNET_ID")
        if subnet_id:
            params["SubnetId"] = subnet_id

        return params

    def create_game_vm(self, user_id: int, game_id: int) -> Dict[str, Any]:
        """
        Crea una instancia EC2 a partir de la AMI de juegos y espera a que arranque.
        Devuelve instance_id y public_ip.
        """
        params = self._build_run_instances_params(user_id=user_id, game_id=game_id)
        instances = self.ec2_resource.create_instances(**params)
        instance = instances[0]

        # Esperar a que esté en running
        instance.wait_until_running()
        instance.reload()

        return {
            "instance_id": instance.id,
            "public_ip": instance.public_ip_address,
            "state": instance.state.get("Name"),
        }
