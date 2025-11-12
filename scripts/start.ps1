Stop-Process -Name uvicorn -ErrorAction SilentlyContinue
$env:APP_ENV="prod"
cd C:\retrocloud\app
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "main:app --host 0.0.0.0 --port 8080"
