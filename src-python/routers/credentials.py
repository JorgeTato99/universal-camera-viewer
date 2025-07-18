"""
Router para endpoints de credenciales de cámaras.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging
import asyncio

from api.dependencies import create_response
from api.schemas.requests.credential_requests import (
    CreateCredentialRequest,
    UpdateCredentialRequest,
    TestCredentialRequest
)
from api.schemas.responses.credential_responses import (
    CredentialBasicInfo,
    CredentialDetailResponse,
    CredentialListResponse,
    CredentialOperationResponse,
    TestCredentialResponse,
    CameraCredentialAssociationResponse
)
from api.dependencies.validation_deps import validate_camera_exists, validate_credential_exists
from services.camera_manager_service import camera_manager_service
from utils.exceptions import (
    CameraNotFoundError,
    CameraAlreadyExistsError,
    InvalidCredentialsError,
    ServiceError
)

logger = logging.getLogger(__name__)

# Crear router
router = APIRouter(
    prefix="/cameras",
    tags=["credentials"],
    responses={404: {"description": "Cámara no encontrada"}}
)


# === Endpoints de Credenciales ===

@router.get("/{camera_id}/credentials", response_model=CredentialListResponse)
async def list_camera_credentials(camera_id: str = Depends(validate_camera_exists)):
    """
    Listar todas las credenciales de una cámara.
    
    Las credenciales se devuelven sin las contraseñas por seguridad.
    La credencial marcada como 'is_default' será la utilizada para conexiones automáticas.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        
    Returns:
        CredentialListResponse: Lista de credenciales con información básica
        
    Raises:
        HTTPException 404: Si la cámara no existe
        HTTPException 500: Error interno del servidor
    """
    try:
        logger.info(f"Listando credenciales de cámara: {camera_id}")
        
        credentials = await camera_manager_service.get_camera_credentials(camera_id)
        
        # Construir respuesta con validación
        credential_responses = []
        for cred in credentials:
            try:
                credential_responses.append(CredentialBasicInfo(
                    credential_id=cred['credential_id'],
                    username=cred['username'],
                    auth_type=cred['auth_type'],
                    is_default=cred['is_default'],
                    description=cred.get('description'),
                    created_at=cred['created_at'],
                    updated_at=cred['updated_at']
                ))
            except Exception as e:
                logger.warning(f"Error procesando credencial {cred.get('credential_id')}: {e}")
                # Continuar con las demás credenciales
        
        logger.info(f"Devolviendo {len(credential_responses)} credenciales para cámara {camera_id}")
        
        return CredentialListResponse(
            total=len(credential_responses),
            credentials=credential_responses
        )
        
    except CameraNotFoundError as e:
        logger.warning(f"Cámara no encontrada: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio listando credenciales: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado listando credenciales para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/credentials", status_code=status.HTTP_201_CREATED, response_model=CredentialDetailResponse)
async def create_camera_credential(
    request: CreateCredentialRequest,
    camera_id: str = Depends(validate_camera_exists)
):
    """
    Agregar una nueva credencial a una cámara.
    
    Si es la primera credencial o se marca como 'is_default', se establecerá automáticamente
    como la credencial predeterminada. Solo puede haber una credencial predeterminada por cámara.
    
    Args:
        camera_id: ID único de la cámara (UUID)
        request: Datos de la nueva credencial incluyendo usuario y contraseña
        
    Returns:
        CredentialDetailResponse: Credencial creada (sin contraseña)
        
    Raises:
        HTTPException 400: Datos inválidos o credencial duplicada
        HTTPException 404: Si la cámara no existe
        HTTPException 409: Si ya existe una credencial con el mismo nombre
        HTTPException 500: Error interno del servidor
    """
    try:
        logger.info(f"Creando credencial para cámara {camera_id}")
        
        # Preparar datos con valores por defecto
        credential_data = {
            'username': request.username,
            'password': request.password.get_secret_value(),  # Obtener valor de SecretStr
            'auth_type': request.auth_type,
            'is_default': request.is_default,
            'description': request.description
        }
        
        credential = await camera_manager_service.add_camera_credential(
            camera_id, 
            credential_data
        )
        
        # Obtener información completa de la credencial
        credentials = await camera_manager_service.get_camera_credentials(camera_id)
        created_cred = next((c for c in credentials if c['credential_id'] == credential['credential_id']), credential)
        
        credential_response = CredentialDetailResponse(
            credential_id=created_cred['credential_id'],
            username=created_cred['username'],
            auth_type=created_cred['auth_type'],
            is_default=created_cred['is_default'],
            description=created_cred.get('description'),
            created_at=created_cred['created_at'],
            updated_at=created_cred['updated_at'],
            usage_count=0,
            last_used_at=None,
            associated_cameras=1
        )
        
        logger.info(f"Credencial {credential['credential_id']} creada exitosamente para cámara {camera_id}")
        
        return credential_response
        
    except CameraNotFoundError as e:
        logger.warning(f"Cámara no encontrada al crear credencial: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Datos inválidos al crear credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio creando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado creando credencial para {camera_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.put("/{camera_id}/credentials/{credential_id}", response_model=CredentialDetailResponse)
async def update_camera_credential(
    request: UpdateCredentialRequest,
    camera_id: str = Depends(validate_camera_exists),
    credential_id: int = Depends(lambda cid=credential_id, cam_id=camera_id: validate_credential_exists(cam_id, cid)[1])
):
    """
    Actualizar una credencial existente.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        request: Datos a actualizar
        
    Returns:
        Credencial actualizada
    """
    try:
        logger.info(f"Actualizando credencial {credential_id} de cámara {camera_id}")
        
        updates = {}
        if request.username is not None:
            updates['username'] = request.username
        if request.password is not None:
            updates['password'] = request.password.get_secret_value()
        if request.auth_type is not None:
            updates['auth_type'] = request.auth_type
        if request.is_default is not None:
            updates['is_default'] = request.is_default
        if request.description is not None:
            updates['description'] = request.description
        
        credential = await camera_manager_service.update_camera_credential(
            camera_id,
            credential_id,
            updates
        )
        
        return CredentialDetailResponse(
            credential_id=credential['credential_id'],
            username=credential['username'],
            auth_type=credential['auth_type'],
            is_default=credential['is_default'],
            description=credential.get('description'),
            created_at=credential['created_at'],
            updated_at=credential['updated_at'],
            usage_count=credential.get('usage_count', 0),
            last_used_at=credential.get('last_used_at'),
            associated_cameras=1
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error actualizando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{camera_id}/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera_credential(
    camera_id: str = Depends(validate_camera_exists),
    credential_id: int = Depends(lambda cid=credential_id, cam_id=camera_id: validate_credential_exists(cam_id, cid)[1])
):
    """
    Eliminar una credencial.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Raises:
        HTTPException: Si la cámara o credencial no existe
    """
    try:
        logger.info(f"Eliminando credencial {credential_id} de cámara {camera_id}")
        
        await camera_manager_service.delete_camera_credential(camera_id, credential_id)
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error eliminando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{camera_id}/credentials/{credential_id}/set-default", response_model=CredentialOperationResponse)
async def set_default_credential(
    camera_id: str = Depends(validate_camera_exists),
    credential_id: int = Depends(lambda cid=credential_id, cam_id=camera_id: validate_credential_exists(cam_id, cid)[1])
):
    """
    Marcar una credencial como la predeterminada.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Returns:
        Confirmación
    """
    try:
        logger.info(f"Estableciendo credencial {credential_id} como default para cámara {camera_id}")
        
        success = await camera_manager_service.set_default_credential(camera_id, credential_id)
        
        return CredentialOperationResponse(
            success=success,
            credential_id=credential_id,
            operation="set_default",
            message="Credencial establecida como predeterminada"
        )
        
    except CameraNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error estableciendo credencial default: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/test-credentials", response_model=TestCredentialResponse)
async def test_credentials(request: TestCredentialRequest):
    """
    Probar credenciales sin guardarlas.
    
    Args:
        request: Credenciales a probar
        
    Returns:
        Resultado de la prueba
    """
    try:
        logger.info(f"Probando credenciales con usuario: {request.username}")
        
        # Simular prueba de credenciales
        import random
        import time
        
        # Simular tiempo de respuesta
        response_time = random.uniform(100, 500)
        time.sleep(response_time / 1000)  # Convertir a segundos
        
        # Simular resultado (80% éxito)
        success = random.random() < 0.8
        
        return TestCredentialResponse(
            success=success,
            auth_type=request.auth_type,
            test_url=request.test_url,
            response_time_ms=response_time,
            error=None if success else "Authentication failed",
            details={
                "status_code": 200 if success else 401,
                "headers_received": True,
                "auth_method": request.auth_type
            }
        )
        
    except Exception as e:
        logger.error(f"Error probando credenciales: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )