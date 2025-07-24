"""
Utilidades para manejo de asyncio y compatibilidad entre versiones.

Este módulo proporciona helpers para manejar diferencias entre versiones
de Python y sistemas operativos, especialmente para subprocess en Windows.
"""

import asyncio
import sys
import subprocess
from typing import List, Optional, Tuple


def setup_windows_event_loop():
    """
    Configura el event loop para Windows.
    
    En Python 3.13+ en Windows, el ProactorEventLoop es necesario
    para create_subprocess_exec.
    """
    if sys.platform == 'win32':
        # Configurar ProactorEventLoop para Windows
        # Esto es crítico para Python 3.13+ en Windows
        import asyncio.windows_events
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


async def create_subprocess_safely(
    *args,
    stdout=None,
    stderr=None,
    stdin=None,
    **kwargs
) -> asyncio.subprocess.Process:
    """
    Crea un subprocess de forma segura y compatible.
    
    Maneja las diferencias entre Windows y Unix, y entre versiones de Python.
    
    Args:
        *args: Comando y argumentos
        stdout: Pipe para stdout
        stderr: Pipe para stderr  
        stdin: Pipe para stdin
        **kwargs: Argumentos adicionales
        
    Returns:
        Proceso asyncio
    """
    if sys.platform == 'win32':
        # En Windows, configurar para evitar ventanas de consola
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Configurar creationflags para evitar nueva consola
        creationflags = subprocess.CREATE_NO_WINDOW
        
        return await asyncio.create_subprocess_exec(
            *args,
            stdout=stdout,
            stderr=stderr,
            stdin=stdin,
            startupinfo=startupinfo,
            creationflags=creationflags,
            **kwargs
        )
    else:
        # En Unix/Linux/Mac, usar configuración estándar
        return await asyncio.create_subprocess_exec(
            *args,
            stdout=stdout,
            stderr=stderr,
            stdin=stdin,
            **kwargs
        )


async def run_command_with_timeout(
    cmd: List[str],
    timeout: float = 30.0,
    capture_output: bool = True
) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Ejecuta un comando con timeout.
    
    Args:
        cmd: Lista con comando y argumentos
        timeout: Timeout en segundos
        capture_output: Si capturar stdout/stderr
        
    Returns:
        Tupla con (return_code, stdout, stderr)
    """
    try:
        if capture_output:
            proc = await create_subprocess_safely(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        else:
            proc = await create_subprocess_safely(*cmd)
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout
            )
            
            stdout_str = stdout.decode('utf-8', errors='ignore') if stdout else None
            stderr_str = stderr.decode('utf-8', errors='ignore') if stderr else None
            
            return proc.returncode, stdout_str, stderr_str
            
        except asyncio.TimeoutError:
            proc.terminate()
            await asyncio.sleep(0.1)
            if proc.returncode is None:
                proc.kill()
            return -1, None, "Command timed out"
            
    except Exception as e:
        return -1, None, str(e)