"""
Router para endpoints de credenciales de cámaras.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime
import logging
import asyncio

from api.dependencies import create_response
from api.models.camera_models import (
    CredentialsResponse,
    CreateCredentialRequest,
    UpdateCredentialRequest,
    CredentialDetailResponse,
    CredentialListResponse,
)
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
async def list_camera_credentials(camera_id: str):
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
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
            
        logger.info(f"Listando credenciales de cámara: {camera_id}")
        
        credentials = await camera_manager_service.get_camera_credentials(camera_id)
        
        # Construir respuesta con validación
        credential_responses = []
        for cred in credentials:
            try:
                credential_responses.append(CredentialDetailResponse(
                    credential_id=cred['credential_id'],
                    credential_name=cred['credential_name'],
                    username=cred['username'],
                    auth_type=cred['auth_type'],
                    is_active=cred['is_active'],
                    is_default=cred['is_default'],
                    last_used=cred.get('last_used'),
                    created_at=cred['created_at'],
                    updated_at=cred['updated_at']
                ))
            except Exception as e:
                logger.warning(f"Error procesando credencial {cred.get('credential_id')}: {e}")
                # Continuar con las demás credenciales
        
        response_data = CredentialListResponse(
            total=len(credential_responses),
            credentials=credential_responses
        )
        
        logger.info(f"Devolviendo {len(credential_responses)} credenciales para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=response_data.dict()
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
    camera_id: str,
    request: CreateCredentialRequest
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
        # Validar formato UUID
        if not camera_id or len(camera_id) != 36:
            logger.warning(f"ID de cámara inválido: {camera_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID de cámara debe ser un UUID válido"
            )
        
        # Validar longitud de contraseña
        if len(request.password) < 4:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña debe tener al menos 4 caracteres"
            )
            
        logger.info(f"Creando credencial '{request.credential_name}' para cámara {camera_id}")
        
        # Preparar datos con valores por defecto
        credential_data = {
            'credential_name': request.credential_name.strip(),
            'username': request.username.strip(),
            'password': request.password,  # No hacer strip a contraseñas
            'auth_type': request.auth_type.value if hasattr(request.auth_type, 'value') else request.auth_type,
            'is_default': request.is_default
        }
        
        # Validar que no haya espacios en el username
        if ' ' in credential_data['username']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario no puede contener espacios"
            )
        
        credential = await camera_manager_service.add_camera_credential(
            camera_id, 
            credential_data
        )
        
        credential_response = CredentialDetailResponse(
            credential_id=credential['credential_id'],
            credential_name=credential['credential_name'],
            username=credential['username'],
            auth_type=credential['auth_type'],
            is_active=credential['is_active'],
            is_default=credential['is_default'],
            last_used=credential.get('last_used'),
            created_at=credential['created_at'],
            updated_at=credential['updated_at']
        )
        
        logger.info(f"Credencial {credential['credential_id']} creada exitosamente para cámara {camera_id}")
        
        return create_response(
            success=True,
            data=credential_response.dict()
        )
        
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


@router.put("/{camera_id}/credentials/{credential_id}")
async def update_camera_credential(
    camera_id: str,
    credential_id: int,
    request: UpdateCredentialRequest
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
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
    
    # Validar credential_id
    if credential_id <= 0:
        logger.warning(f"ID de credencial inválido: {credential_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de credencial debe ser un número positivo"
        )
    
    try:
        logger.info(f"Actualizando credencial {credential_id} de cámara {camera_id}")
        
        # Preparar actualizaciones con validación
        updates = {}
        if request.credential_name is not None:
            updates['credential_name'] = request.credential_name.strip()
            if not updates['credential_name']:
                raise ValueError("El nombre de la credencial no puede estar vacío")
                
        if request.username is not None:
            updates['username'] = request.username.strip()
            if ' ' in updates['username']:
                raise ValueError("El nombre de usuario no puede contener espacios")
                
        if request.password is not None and request.password:
            if len(request.password) < 4:
                raise ValueError("La contraseña debe tener al menos 4 caracteres")
            updates['password'] = request.password
            
        if request.auth_type is not None:
            updates['auth_type'] = request.auth_type.value if hasattr(request.auth_type, 'value') else request.auth_type
            
        if request.is_default is not None:
            updates['is_default'] = request.is_default
        
        # Verificar que hay algo que actualizar
        if not updates:
            logger.warning(f"No se proporcionaron datos para actualizar credencial {credential_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron datos para actualizar"
            )
        
        credential = await camera_manager_service.update_camera_credential(
            camera_id,
            credential_id,
            updates
        )
        
        credential_response = CredentialDetailResponse(
            credential_id=credential['credential_id'],
            credential_name=credential['credential_name'],
            username=credential['username'],
            auth_type=credential['auth_type'],
            is_active=credential['is_active'],
            is_default=credential['is_default'],
            last_used=credential.get('last_used'),
            created_at=credential['created_at'],
            updated_at=credential['updated_at']
        )
        
        logger.info(f"Credencial {credential_id} actualizada exitosamente")
        
        return create_response(
            success=True,
            data=credential_response.dict()
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada al actualizar credencial: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Error de validación actualizando credencial: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-lanzar excepciones HTTP sin modificar
        raise
    except ServiceError as e:
        logger.error(f"Error de servicio actualizando credencial {credential_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado actualizando credencial {credential_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.delete("/{camera_id}/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera_credential(
    camera_id: str,
    credential_id: int
):
    """
    Eliminar una credencial.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Raises:
        HTTPException: Si la cámara o credencial no existe
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
    
    # Validar credential_id
    if credential_id <= 0:
        logger.warning(f"ID de credencial inválido: {credential_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de credencial debe ser un número positivo"
        )
    
    try:
        logger.info(f"Eliminando credencial {credential_id} de cámara {camera_id}")
        
        await camera_manager_service.delete_camera_credential(camera_id, credential_id)
        
        logger.info(f"Credencial {credential_id} eliminada exitosamente")
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada al eliminar credencial: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Credencial no encontrada: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credencial {credential_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio eliminando credencial {credential_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado eliminando credencial {credential_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{camera_id}/credentials/{credential_id}/set-default")
async def set_default_credential(
    camera_id: str,
    credential_id: int
):
    """
    Marcar una credencial como la predeterminada.
    
    Args:
        camera_id: ID de la cámara
        credential_id: ID de la credencial
        
    Returns:
        Confirmación
    """
    # Validar formato UUID
    if not camera_id or len(camera_id) != 36:
        logger.warning(f"ID de cámara inválido: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de cámara debe ser un UUID válido"
        )
    
    # Validar credential_id
    if credential_id <= 0:
        logger.warning(f"ID de credencial inválido: {credential_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de credencial debe ser un número positivo"
        )
    
    try:
        logger.info(f"Estableciendo credencial {credential_id} como default para cámara {camera_id}")
        
        success = await camera_manager_service.set_default_credential(camera_id, credential_id)
        
        if success:
            logger.info(f"Credencial {credential_id} establecida como predeterminada exitosamente")
        else:
            logger.warning(f"No se pudo establecer credencial {credential_id} como predeterminada")
        
        return create_response(
            success=success,
            data={
                "camera_id": camera_id,
                "credential_id": credential_id,
                "message": "Credencial establecida como predeterminada" if success else "No se pudo establecer como predeterminada"
            }
        )
        
    except CameraNotFoundError:
        logger.warning(f"Cámara no encontrada al establecer credencial default: {camera_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cámara {camera_id} no encontrada"
        )
    except ValueError as e:
        logger.warning(f"Credencial no encontrada: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credencial {credential_id} no encontrada"
        )
    except ServiceError as e:
        logger.error(f"Error de servicio estableciendo credencial default: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio temporalmente no disponible"
        )
    except Exception as e:
        logger.error(f"Error inesperado estableciendo credencial default: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )