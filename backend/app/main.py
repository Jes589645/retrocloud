import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <--- NUEVO
from fastapi.responses import FileResponse # <--- NUEVO
from pydantic import BaseModel
from botocore.exceptions import ClientError
import os

app = FastAPI()

# CORS (Ya no es estrictamente necesario si servimos desde el mismo origen, pero lo dejamos por seguridad)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TUS CONFIGURACIONES ---
AMI_ID = "ami-0a6b5b6ae84396647"
SUBNET_ID = "subnet-09a1953a7d957d51b"
SECURITY_GROUP_ID = "sg-0487e9a61303171db"
KEY_NAME = "keypairinfti"

ec2 = boto3.client('ec2', region_name='us-east-2')

class GameSession(BaseModel):
    game_filename: str

@app.post("/games/session")
def create_session(session: GameSession):
    # ... (TU CÓDIGO DE CREACIÓN DE SESIÓN SE MANTIENE IGUAL) ...
    # (Copio solo el inicio para referencia, no borres tu lógica de UserData)
    print(f"🚀 Lanzando sesión para: {session.game_filename}")
    
    user_data_script = f"""<powershell>
    $Pass = "RetroCloudRules!2025"
    net user Administrator $Pass
    # ... (Resto de tu script PowerShell) ...
    # ... Asegúrate de tener el script completo aquí ...
    </powershell>
    """
    
    # ... (Lógica de run_instances igual) ...
    
    # MOCK RETURN para pruebas si no quieres lanzar instancias reales cada vez
    # return {"status": "mock", "url": "https://fake-url:8443", "user": "Admin", "pass": "123"} 
    
    # Lógica REAL (descomentar si tienes el código completo)
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
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        desc = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = desc['Reservations'][0]['Instances'][0].get('PublicIpAddress')
        
        return {
            "status": "ready",
            "url": f"https://{public_ip}:8443",
            "user": "Administrator",
            "pass": "RetroCloudRules!2025"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/sessions/{instance_id}")
def end_session(instance_id: str):
    ec2.terminate_instances(InstanceIds=[instance_id])
    return {"status": "terminated"}

# --- NUEVO: SERVIR FRONTEND ---

# 1. Servir archivos estáticos (JS, CSS, Imágenes)
# Asegúrate de que la ruta sea correcta relativo a donde corres uvicorn
app.mount("/assets", StaticFiles(directory="app/static/assets"), name="assets")

# 2. Servir el HTML principal en la raíz (o en /ui si prefieres)
@app.get("/") # O @app.get("/ui")
async def serve_ui():
    return FileResponse('app/static/index.html')
