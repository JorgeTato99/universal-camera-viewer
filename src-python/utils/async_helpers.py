"""
Utilidades para manejo de asyncio y compatibilidad entre versiones.

Este módulo proporciona helpers para manejar diferencias entre versiones
de Python y sistemas operativos, especialmente para subprocess en Windows.
"""

import asyncio
import sys
import subprocess
import logging
from typing import List, Optional, Tuple

# Configurar logger
logger = logging.getLogger(__name__)

# Importar ProactorEventLoop para verificación de tipo
if sys.platform == 'win32':
    from asyncio.windows_events import ProactorEventLoop


class StreamReaderWrapper:
    """Wrapper para streams de subprocess que simula asyncio.StreamReader."""
    
    def __init__(self, stream):
        self._stream = stream
        self._loop = None
    
    async def readline(self):
        """Lee una línea del stream de forma asíncrona."""
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        
        if self._stream is None:
            return b''
        
        # Leer en un executor para no bloquear
        line = await self._loop.run_in_executor(None, self._stream.readline)
        return line
    
    async def read(self, n=-1):
        """Lee n bytes del stream de forma asíncrona."""
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        
        if self._stream is None:
            return b''
        
        # Leer en un executor para no bloquear
        data = await self._loop.run_in_executor(None, self._stream.read, n)
        return data


class SubprocessWrapper:
    """
    Wrapper para subprocess.Popen que simula la interfaz de asyncio.subprocess.Process.
    
    Usado en Windows para evitar problemas con el event loop.
    """
    
    def __init__(self, process: subprocess.Popen):
        self._process = process
        self.pid = process.pid
        # Envolver los streams
        self.stdout = StreamReaderWrapper(process.stdout) if process.stdout else None
        self.stderr = StreamReaderWrapper(process.stderr) if process.stderr else None
    
    @property
    def returncode(self):
        """Obtiene el código de retorno del proceso."""
        return self._process.poll()
    
    async def wait(self):
        """Espera a que el proceso termine."""
        loop = asyncio.get_running_loop()
        # Ejecutar wait() en un thread para no bloquear
        returncode = await loop.run_in_executor(None, self._process.wait)
        return returncode
    
    def terminate(self):
        """Termina el proceso."""
        try:
            self._process.terminate()
        except:
            pass
    
    def kill(self):
        """Mata el proceso."""
        try:
            self._process.kill()
        except:
            pass
    
    async def communicate(self, input=None):
        """Lee stdout y stderr del proceso."""
        loop = asyncio.get_running_loop()
        stdout, stderr = await loop.run_in_executor(
            None, self._process.communicate, input
        )
        return stdout, stderr


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
):
    """
    Crea un subprocess de forma segura y compatible.
    
    Maneja las diferencias entre Windows y Unix, y entre versiones de Python.
    En Windows, usa un enfoque diferente para evitar problemas con el event loop.
    
    Args:
        *args: Comando y argumentos
        stdout: Pipe para stdout
        stderr: Pipe para stderr  
        stdin: Pipe para stdin
        **kwargs: Argumentos adicionales
        
    Returns:
        Proceso (asyncio.subprocess.Process o SubprocessWrapper en Windows)
    """
    if sys.platform == 'win32':
        # En Windows, usar subprocess.Popen con un wrapper
        # para evitar problemas con ProactorEventLoop
        
        # Configurar para evitar ventanas de consola
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Configurar creationflags para evitar nueva consola
        creationflags = subprocess.CREATE_NO_WINDOW
        
        # Crear el proceso con subprocess.Popen
        proc = subprocess.Popen(
            args,
            stdout=stdout if stdout == subprocess.PIPE else None,
            stderr=stderr if stderr == subprocess.PIPE else None,
            stdin=subprocess.DEVNULL,  # Siempre usar DEVNULL para stdin
            startupinfo=startupinfo,
            creationflags=creationflags,
            **kwargs
        )
        
        # Retornar un wrapper que simula asyncio.subprocess.Process
        return SubprocessWrapper(proc)
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