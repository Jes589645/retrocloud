import os
import time
from typing import Tuple

import boto3


class GameOrchestrator:
    def __init__(
        self,
        ami_id: str,
        region_name: str = None,
        instance_type: str = None,
    ):
        """
        Orquestador de VMs de juego.

        :param ami_id: ID de la AMI de juegos (GAME_AMI_ID)
        :param region_name: Región AWS, por defecto GAME_AWS_REGION o us-east-2
        :param instance_type: Tipo de instancia, por defecto GAME_INSTANCE_TYPE o m7i-flex.large
        """
        self.ami_id = ami_id
        self.region_name = region_name or os.getenv("GAME_AWS_REGION", "us-east-2")
        self.instance_type = instance_type or os.getenv("GAME_INSTANCE_TYPE", "m7i-flex.large")

        # Nombre de keypair (en AWS) para poder acceder por SSH/RDP si hace falta
        # Usa el que ya tienes creado: keypairinfti
        self.key_name = os.getenv("GAME_KEY_NAME", "keypairinfti")

        # Cliente EC2
        self.ec2 = boto3.client("ec2", region_name=self.region_name)

    def launch_game_vm(self, rom_filename: str, console: str = "SNES") -> Tuple[str, str]:
        """
        Lanza una nueva instancia de juego basada en la AMI y arranca RetroArch
        con la ROM indicada.

        :param rom_filename: Nombre del archivo de la ROM (por ejemplo "ActRaiser 2.smc")
        :param console: Nombre de la consola (por ejemplo "SNES")
        :return: (instance_id, public_ip)
        """

        # Ruta donde están las ROMs dentro de la VM de juego.
        # En tu AMI las dejaste en /home/ubuntu/roms/roms/snes/
        rom_path = f"/home/ubuntu/roms/roms/snes/{rom_filename}"

        # Script de user-data que se ejecuta en el primer arranque de la instancia.
        # Ajusta el comando si en tu VM el comando correcto para lanzar RetroArch es distinto.
        user_data_script = f"""#!/bin/bash
# Esperar a que el sistema termine de levantar servicios básicos
sleep 20

# Exportar DISPLAY para el entorno gráfico
export DISPLAY=:0

# Lanzar RetroArch como el usuario ubuntu con la ROM especificada.
# Si necesitas especificar un core concreto, añade -L /ruta/al/core_libretro.so.
su - ubuntu -c 'DISPLAY=:0 flatpak run org.libretro.RetroArch "{rom_path}"' &

"""

        print(f"[INFO] Lanzando VM de juego con AMI {self.ami_id}, ROM {rom_path}")

        # Llamada a run_instances SIN TagSpecifications, para no requerir ec2:CreateTags
        run_args = {
            "ImageId": self.ami_id,
            "InstanceType": self.instance_type,
            "MinCount": 1,
            "MaxCount": 1,
            "KeyName": self.key_name,
            "UserData": user_data_script,
        }

        response = self.ec2.run_instances(**run_args)

        instance = response["Instances"][0]
        instance_id = instance["InstanceId"]

        print(f"[INFO] Instancia de juego creada: {instance_id}, esperando a que esté 'running'...")

        # Esperar a que la instancia pase a estado "running"
        waiter = self.ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=[instance_id])

        # Esperar un poco más a que reciba IP pública
        time.sleep(5)

        desc = self.ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = desc["Reservations"][0]["Instances"][0].get("PublicIpAddress")

        print(f"[INFO] Instancia {instance_id} en ejecución con IP pública {public_ip}")

        return instance_id, public_ip
