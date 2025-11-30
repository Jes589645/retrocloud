import boto3
import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from botocore.exceptions import ClientError

app = FastAPI()

# --- CONFIGURACIÓN DE RUTAS ESTÁTICAS (FRONTEND) ---
# Detecta la ruta absoluta de donde está este archivo main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")

# Verificar si la carpeta static existe (Debug)
if not os.path.exists(STATIC_DIR):
    print(f"⚠️ ADVERTENCIA CRÍTICA: No encuentro la carpeta {STATIC_DIR}")
    print("Asegúrate de haber copiado el build del frontend aquí.")
else:
    print(f"✅ Carpeta estática encontrada en: {STATIC_DIR}")

# Montar carpeta de assets (JS/CSS generados por Vite)
# Solo si existe, para evitar crash al inicio si falta el build
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Servir el HTML principal en la raíz
@app.get("/")
async def serve_spa():
    if os.path.exists(os.path.join(STATIC_DIR, "index.html")):
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
    return {"error": "Frontend not built. Please run 'npm run build' and copy dist to app/static"}

# --- CONFIGURACIÓN DE AWS (BACKEND) ---
# IDs fijos de tu infraestructura en Ohio
AMI_ID = "ami-0a6b5b6ae84396647"
SUBNET_ID = "subnet-09a1953a7d957d51b"
SECURITY_GROUP_ID = "sg-0487e9a61303171db"
KEY_NAME = "keypairinfti"

ec2 = boto3.client('ec2', region_name='us-east-2')

# CORS habilitado para desarrollo local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameSession(BaseModel):
    game_filename: str

@app.post("/games/session")
def create_session(session: GameSession):
    print(f"🚀 Lanzando sesión para: {session.game_filename}")
    
    # Script PowerShell que se ejecuta dentro de la VM Windows al nacer
    user_data_script = f"""<powershell>
    # 1. Credenciales y Autologin
    $Pass = "RetroCloudRules!2025"
    net user Administrator $Pass
    $Reg = "HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Winlogon"
    New-ItemProperty -Path $Reg -Name "AutoAdminLogon" -Value "1" -PropertyType String -Force
    New-ItemProperty -Path $Reg -Name "DefaultUserName" -Value "Administrator" -PropertyType String -Force
    New-ItemProperty -Path $Reg -Name "DefaultPassword" -Value $Pass -PropertyType String -Force
    
    # 2. Firewall para DCV
    New-NetFirewallRule -DisplayName "DCV Web" -Direction Inbound -LocalPort 8443 -Protocol TCP -Action Allow

    # 3. Configurar Juego
    $Retro = "C:\\Program Files\\RetroArch\\retroarch.exe"
    $Core = "C:\\Program Files\\RetroArch\\cores\\snes9x_libretro.dll"
    $Rom = "C:\\RetroCloud\\Roms\\{session.game_filename}"
    
    # 4. Tarea Programada (Arranca al inicio de sesión)
    $Action = New-ScheduledTaskAction -Execute $Retro -Argument "-L `"$Core`" `"$Rom`" -f"
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    Register-ScheduledTask -TaskName "PlayGame" -Trigger $Trigger -Action $Action -User "Administrator" -RunLevel Highest
    
    # 5. Reiniciar servicio DCV
    Restart-Service dcvserver
    </powershell>
    """

    try:
        instance = ec2.run_instances(
            ImageId=AMI_ID,
            InstanceType='m7i-flex.large',
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME,
            SubnetId=SUBNET_ID,
            SecurityGroupIds=[SECURITY_GROUP_ID],
            UserData=user_data_script,
            TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'RetroSession'}]}]
        )
        
        instance_id = instance['Instances'][0]['InstanceId']
        
        # Esperar a que tenga IP (Polling rápido)
        print(f"⏳ Esperando IP para {instance_id}...")
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        desc = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = desc['Reservations'][0]['Instances'][0]['PublicIpAddress']

        return {
            "status": "ready",
            "url": f"https://{public_ip}:8443",
            "user": "Administrator",
            "pass": "RetroCloudRules!2025"
        }

    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{instance_id}")
def end_session(instance_id: str):
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        return {"status": "terminated"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))
