"""
Router API para autenticación con servidores MediaMTX remotos.

Expone endpoints para:
- Login/logout de servidores
- Consulta de estado de autenticación
- Validación de conexiones
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from presenters.mediamtx_auth_presenter import get_mediamtx_auth_presenter
from api.dependencies import create_response
from services.logging_service import get_secure_logger


logger = get_secure_logger("api.routers.mediamtx_auth")


# === Modelos Pydantic ===

class LoginRequest(BaseModel):
    """Solicitud de login a servidor MediaMTX."""
    server_id: int = Field(..., description="ID del servidor MediaMTX")
    username: str = Field(..., description="Nombre de usuario")
    password: str = Field(..., description="Contraseña")
    
    class Config:
        json_schema_extra = {
            "example": {
                "server_id": 1,
                "username": "admin",
                "password": "secure_password"
            }
        }


class LoginResponse(BaseModel):
    """Respuesta de login."""
    success: bool
    server_id: int
    server_name: str
    message: Optional[str] = None
    error: Optional[str] = None


class LogoutRequest(BaseModel):
    """Solicitud de logout."""
    server_id: int = Field(..., description="ID del servidor MediaMTX")


class AuthStatusResponse(BaseModel):
    """Estado de autenticación de un servidor."""
    success: bool
    server_id: Optional[int] = None
    server_name: Optional[str] = None
    api_url: Optional[str] = None
    is_authenticated: Optional[bool] = None
    last_check: Optional[str] = None
    last_error: Optional[str] = None
    error: Optional[str] = None


class AllServersAuthStatus(BaseModel):
    """Estado de autenticación de todos los servidores."""
    success: bool
    servers: Optional[list] = None
    authenticated_count: Optional[int] = None
    total_count: Optional[int] = None
    error: Optional[str] = None


# === Router ===

router = APIRouter(
    prefix="/api/mediamtx/auth",
    tags=["mediamtx-auth"],
    responses={
        404: {"description": "Servidor no encontrado"},
        401: {"description": "Credenciales inválidas"}
    }
)


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Autenticar con servidor MediaMTX",
    description="Realiza login con un servidor MediaMTX remoto y almacena el token JWT"
)
async def login(
    request: LoginRequest,
    presenter = Depends(get_mediamtx_auth_presenter)
) -> LoginResponse:
    """
    Autentica con un servidor MediaMTX remoto.
    
    El token JWT obtenido se almacena de forma segura y se usa
    automáticamente en las operaciones posteriores con el servidor.
    """
    logger.info(f"Login request para servidor {request.server_id}")
    
    try:
        result = await presenter.authenticate_server(
            server_id=request.server_id,
            username=request.username,
            password=request.password
        )
        
        if not result['success']:
            # Determinar código de error apropiado
            if 'no encontrado' in result.get('error', '').lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result['error']
                )
            elif 'credenciales' in result.get('error', '').lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result['error']
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get('error', 'Error de autenticación')
                )
        
        return LoginResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post(
    "/logout",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión de servidor MediaMTX",
    description="Invalida el token JWT almacenado para el servidor"
)
async def logout(
    request: LogoutRequest,
    presenter = Depends(get_mediamtx_auth_presenter)
) -> LoginResponse:
    """
    Cierra la sesión con un servidor MediaMTX.
    
    Elimina el token almacenado y cancela cualquier operación
    de refresco automático.
    """
    logger.info(f"Logout request para servidor {request.server_id}")
    
    try:
        result = await presenter.logout_server(request.server_id)
        
        if not result['success']:
            if 'no encontrado' in result.get('error', '').lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result['error']
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get('error', 'Error al cerrar sesión')
                )
        
        return LoginResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/status/{server_id}",
    response_model=AuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener estado de autenticación",
    description="Consulta si hay una sesión activa con el servidor"
)
async def get_auth_status(
    server_id: int,
    presenter = Depends(get_mediamtx_auth_presenter)
) -> AuthStatusResponse:
    """
    Obtiene el estado de autenticación de un servidor específico.
    
    Indica si hay un token válido almacenado y cuándo fue la
    última verificación.
    """
    logger.debug(f"Consultando estado de autenticación para servidor {server_id}")
    
    try:
        result = await presenter.get_auth_status(server_id)
        
        if not result['success']:
            if 'no encontrado' in result.get('error', '').lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result['error']
                )
        
        return AuthStatusResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.get(
    "/status",
    response_model=AllServersAuthStatus,
    status_code=status.HTTP_200_OK,
    summary="Obtener estado de todos los servidores",
    description="Lista el estado de autenticación de todos los servidores configurados"
)
async def get_all_auth_status(
    presenter = Depends(get_mediamtx_auth_presenter)
) -> AllServersAuthStatus:
    """
    Obtiene el estado de autenticación de todos los servidores.
    
    Útil para mostrar un dashboard con el estado general del sistema.
    """
    logger.debug("Consultando estado de autenticación global")
    
    try:
        result = await presenter.get_auth_status()
        return AllServersAuthStatus(**result)
        
    except Exception as e:
        logger.error(f"Error obteniendo estado global: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post(
    "/validate/{server_id}",
    response_model=AuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar conexión con servidor",
    description="Verifica que el token almacenado sigue siendo válido"
)
async def validate_connection(
    server_id: int,
    presenter = Depends(get_mediamtx_auth_presenter)
) -> AuthStatusResponse:
    """
    Valida la conexión con un servidor MediaMTX.
    
    Verifica que el token almacenado sigue siendo válido
    realizando una petición de prueba a la API.
    """
    logger.info(f"Validando conexión con servidor {server_id}")
    
    try:
        result = await presenter.validate_server_connection(server_id)
        
        if not result['success']:
            # Si necesita autenticación, devolver 401
            if result.get('needs_auth'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=result.get('error', 'Autenticación requerida')
                )
        
        return AuthStatusResponse(
            success=result['success'],
            server_id=server_id,
            is_authenticated=result.get('is_authenticated', False),
            message=result.get('message'),
            error=result.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validando conexión: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refrescar estado de autenticación",
    description="Actualiza el estado de autenticación de todos los servidores"
)
async def refresh_auth_status(
    presenter = Depends(get_mediamtx_auth_presenter)
) -> Dict[str, Any]:
    """
    Refresca el estado de autenticación.
    
    Útil para forzar una actualización del estado en el presenter.
    """
    logger.info("Refrescando estado de autenticación global")
    
    try:
        await presenter.refresh_auth_status()
        
        return {
            "success": True,
            "message": "Estado de autenticación actualizado"
        }
        
    except Exception as e:
        logger.error(f"Error refrescando estado: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )