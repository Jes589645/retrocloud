import boto3
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from botocore.exceptions import ClientError

app = FastAPI()

# Permitir CORS para que el Frontend (React) pueda hablar con este Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ec2 = boto3.client('ec2', region_name='us-east-2')

# --- TUS CONFIGURACIONES DE PRODUCCIÓN ---
AMI_ID = "ami-0a6b5b6ae84396647"
SUBNET_ID = "subnet-09a1953a7d957d51b"
SECURITY_GROUP_ID = "sg-0487e9a61303171db"
KEY_NAME = "keypairinfti"

class GameSession(BaseModel):
    game_filename: str # Ej: "SuperMarioWorld.smc"

@app.post("/games/session")
def create_session(session: GameSession):
    print(f"🚀 Lanzando sesión para: {session.game_filename}")
    
    # Script Maestro que se ejecutará DENTRO de la nueva VM al nacer
    user_data_script = f"""<powershell>
    # 1. Definir variables
    $Pass = "RetroCloudRules!2025"
    $RetroExe = "C:\\Program Files\\RetroArch\\retroarch.exe"
    $Core = "C:\\Program Files\\RetroArch\\cores\\snes9x_libretro.dll"
    $Rom = "C:\\RetroCloud\\Roms\\{session.game_filename}"

    # 2. Configurar Usuario y Autologin (Crítico para DCV)
    net user Administrator $Pass
    $Reg = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon"
    New-ItemProperty -Path $Reg -Name "AutoAdminLogon" -Value "1" -PropertyType String -Force
    New-ItemProperty -Path $Reg -Name "DefaultUserName" -Value "Administrator" -PropertyType String -Force
    New-ItemProperty -Path $Reg -Name "DefaultPassword" -Value $Pass -PropertyType String -Force

    # 3. Abrir Firewall para DCV (Puerto 8443 TCP)
    New-NetFirewallRule -DisplayName "DCV Web Stream" -Direction Inbound -LocalPort 8443 -Protocol TCP -Action Allow

    # 4. Programar el Juego al Inicio
    # Usamos una Scheduled Task para que arranque en el escritorio interactivo
    $Arg = "-L `"$Core`" `"$Rom`" -f"
    $Action = New-ScheduledTaskAction -Execute $RetroExe -Argument $Arg
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    Register-ScheduledTask -TaskName "LaunchGame" -Trigger $Trigger -Action $Action -User "Administrator" -RunLevel Highest

    # 5. Asegurar que el servicio DCV reinicie para tomar la nueva password
    Restart-Service dcvserver
    </powershell>
    """

    try:
        # Lanzar la instancia
        instance = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType='m7i-flex.large', # Potencia suficiente
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME,
            SubnetId=SUBNET_ID,
            SecurityGroupIds=[SECURITY_GROUP_ID],
            UserData=user_data_script,
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': f'RetroSession-{session.game_filename}'}]}]
        )
        
        instance_id = instance['Instances'][0]['InstanceId']
        print(f"⏳ Instancia {instance_id} creada. Esperando IP pública...")
        
        # Esperar brevemente a que AWS asigne la IP (esto es rápido)
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        desc = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')

        if not public_ip:
            raise HTTPException(status_code=500, detail="No se asignó IP pública")

        return {
            "status": "booting",
            "instance_id": instance_id,
            "url": f"https://{public_ip}:8443",
            "user": "Administrator",
            "pass": "RetroCloudRules!2025",
            "message": "Espera 2-3 minutos a que Windows inicie y luego abre el link."
        }

    except ClientError as e:
        print(f"❌ Error AWS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{instance_id}")
def end_session(instance_id: str):
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        return {"status": "terminated", "id": instance_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
