Set-ExecutionPolicy Bypass -Scope Process -Force
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
  Set-ExecutionPolicy Bypass -Scope Process -Force
  [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
  Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}
choco install -y python --version=3.11.9
$env:Path += ";C:\Python311\Scripts;C:\Python311\"
pip install -r C:\retrocloud\app\requirements.txt
# crea servicio con NSSM si quieres; aquí lo dejamos simple
