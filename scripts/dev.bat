@echo off
echo [STARTING] Iniciando servidores de desarrollo...
echo.

REM Iniciar FastAPI en una nueva ventana
echo [PYTHON] Iniciando servidor FastAPI...
start "FastAPI Server" cmd /k "cd /d %~dp0\..\src-python && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"

REM Esperar un poco para que FastAPI inicie
timeout /t 3 /nobreak > nul

REM Iniciar Vite en una nueva ventana
echo [REACT] Iniciando servidor Vite...
start "Vite Dev Server" cmd /k "cd /d %~dp0\.. && yarn dev"

echo.
echo [SUCCESS] Servidores iniciados:
echo - FastAPI: http://localhost:8000 (API)
echo - FastAPI Docs: http://localhost:8000/docs
echo - Vite: http://localhost:5173 (Frontend)
echo.
echo Presiona cualquier tecla para cerrar este script (los servidores seguiran ejecutandose)...
pause > nul