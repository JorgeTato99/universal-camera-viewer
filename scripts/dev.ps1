# Script de desarrollo para ejecutar FastAPI y Vite

Write-Host "[STARTING] Iniciando servidores de desarrollo..." -ForegroundColor Green
Write-Host ""

# Obtener directorio del proyecto
$projectDir = Split-Path -Parent $PSScriptRoot

# Iniciar FastAPI
Write-Host "[PYTHON] Iniciando servidor FastAPI..." -ForegroundColor Yellow
$fastApiJob = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory "$projectDir\src-python" -PassThru

# Esperar un poco para que FastAPI inicie
Start-Sleep -Seconds 3

# Iniciar Vite
Write-Host "[REACT] Iniciando servidor Vite..." -ForegroundColor Yellow
$viteJob = Start-Process -FilePath "yarn" -ArgumentList "dev" -WorkingDirectory $projectDir -PassThru

Write-Host ""
Write-Host "[SUCCESS] Servidores iniciados:" -ForegroundColor Green
Write-Host "- FastAPI: http://localhost:8000 (API)" -ForegroundColor Cyan
Write-Host "- FastAPI Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "- Vite: http://localhost:5173 (Frontend)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Ctrl+C para detener los servidores..." -ForegroundColor Yellow

# Mantener el script ejecutándose
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Detener procesos al salir
    if ($fastApiJob -and !$fastApiJob.HasExited) {
        Stop-Process -Id $fastApiJob.Id -Force
    }
    if ($viteJob -and !$viteJob.HasExited) {
        Stop-Process -Id $viteJob.Id -Force
    }
}