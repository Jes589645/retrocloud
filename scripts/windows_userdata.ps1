<powershell>
Set-ExecutionPolicy Bypass -Scope Process -Force
# Chocolatey
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  Invoke-Expression ((New-Object Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# Básicos
choco install -y git 7zip python winfsp rclone
# NICE DCV Server
choco install -y nicedcv --version=2024.1.0 # (o la más reciente disponible)
# RetroBat
# Descarga e instala RetroBat (zip); ejemplo:
$rb = "C:\retrobat"
mkdir $rb -ea 0 | Out-Null
Invoke-WebRequest -Uri "https://retrobat.org/retrobat-last.zip" -OutFile "C:\retrobat.zip"
7z x C:\retrobat.zip -o$rb -y

# Montaje S3 con rclone (leerá rclone.conf de C:\retrocloud\scripts cuando llegue el deploy)
# CodeDeploy Agent
cd C:\
Invoke-WebRequest -Uri https://aws-codedeploy-us-east-2.s3.us-east-2.amazonaws.com/latest/codedeploy-agent.msi -OutFile C:\codedeploy-agent.msi
Start-Process msiexec.exe -ArgumentList '/i C:\codedeploy-agent.msi /quiet /qn /norestart' -Wait

# Abrir firewall para 8080 (FastAPI) ya que usaremos el portal en 8080
New-NetFirewallRule -DisplayName "retrocloud-app-8080" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8080
</powershell>
