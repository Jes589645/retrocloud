from datetime import datetime, timedelta
from typing import Optional

import boto3
from sqlalchemy.orm import Session

from .models import GameVM

# Aquí fijo algunos valores; luego puedes pasarlos por env
AWS_REGION = "us-east-2"
INSTANCE_TYPE = "m7i-flex.large"
AMI_ID = None  # Puedes crear una AMI específica para VMs de juego
IDLE_TIMEOUT_MINUTES = 20

ec2 = boto3.client("ec2", region_name=AWS_REGION)


def get_or_create_vm(db: Session, max_sessions: int) -> GameVM:
    """
    Busca una VM con capacidad disponible.
    Si no hay, crea una nueva instancia EC2 y la registra.
    """
    vm = (
        db.query(GameVM)
        .filter(GameVM.status == "running", GameVM.current_sessions < GameVM.max_sessions)
        .first()
    )
    if vm:
        return vm

    # Crear una nueva instancia EC2 para juegos (simplificado)
    if AMI_ID is None:
        # En un PoC, podrías usar la misma AMI de Ubuntu y luego configurar manualmente
        raise RuntimeError("Debes configurar AMI_ID para las VMs de juego")

    response = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        # key_name y sg se pueden fijar por LaunchTemplate o parámetros
    )
    instance = response["Instances"][0]
    instance_id = instance["InstanceId"]

    vm = GameVM(
        instance_id=instance_id,
        status="starting",
        current_sessions=0,
        max_sessions=max_sessions,
        last_activity=datetime.utcnow(),
    )
    db.add(vm)
    db.commit()
    db.refresh(vm)
    return vm


def mark_vm_running(db: Session, vm: GameVM):
    vm.status = "running"
    db.commit()


def register_activity(db: Session, vm: GameVM):
    vm.last_activity = datetime.utcnow()
    db.commit()


def cleanup_idle_vms(db: Session):
    threshold = datetime.utcnow() - timedelta(minutes=IDLE_TIMEOUT_MINUTES)
    idle_vms = (
        db.query(GameVM)
        .filter(
            GameVM.current_sessions == 0,
            GameVM.status == "running",
            GameVM.last_activity < threshold,
        )
        .all()
    )

    for vm in idle_vms:
        try:
            ec2.stop_instances(InstanceIds=[vm.instance_id])
            vm.status = "stopped"
            db.commit()
        except Exception:
            # Podrías loguear el error
            pass
