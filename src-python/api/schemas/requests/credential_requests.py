"""
Schemas de request para endpoints de credenciales.

Modelos Pydantic para validar datos de entrada en credenciales.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator, SecretStr
from api.validators import validate_username, validate_password


class CreateCredentialRequest(BaseModel):
    """Request para crear nueva credencial."""
    
    username: str = Field(..., description="Nombre de usuario")
    password: SecretStr = Field(..., description="Contraseña")
    auth_type: str = Field("basic", description="Tipo de autenticación")
    is_default: bool = Field(False, description="Si es la credencial por defecto")
    description: Optional[str] = Field(None, description="Descripción de la credencial")
    
    @validator('username')
    def validate_username_field(cls, v):
        """Valida el nombre de usuario."""
        return validate_username(v)
    
    @validator('password')
    def validate_password_field(cls, v):
        """Valida la contraseña."""
        if v:
            # SecretStr.get_secret_value() para obtener el valor real
            validate_password(v.get_secret_value())
        return v
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        """Valida el tipo de autenticación."""
        valid_types = ['basic', 'digest', 'bearer', 'custom']
        if v not in valid_types:
            raise ValueError(f"Tipo de autenticación debe ser uno de: {', '.join(valid_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "secure_password",
                "auth_type": "digest",
                "is_default": True,
                "description": "Credenciales principales del administrador"
            }
        }


class UpdateCredentialRequest(BaseModel):
    """Request para actualizar credencial existente."""
    
    username: Optional[str] = Field(None, description="Nuevo nombre de usuario")
    password: Optional[SecretStr] = Field(None, description="Nueva contraseña")
    auth_type: Optional[str] = Field(None, description="Nuevo tipo de autenticación")
    is_default: Optional[bool] = Field(None, description="Si es la credencial por defecto")
    description: Optional[str] = Field(None, description="Nueva descripción")
    
    @validator('username')
    def validate_username_field(cls, v):
        """Valida el nombre de usuario si se proporciona."""
        if v is not None:
            return validate_username(v)
        return v
    
    @validator('password')
    def validate_password_field(cls, v):
        """Valida la contraseña si se proporciona."""
        if v is not None:
            validate_password(v.get_secret_value())
        return v
    
    @validator('auth_type')
    def validate_auth_type(cls, v):
        """Valida el tipo de autenticación si se proporciona."""
        if v is not None:
            valid_types = ['basic', 'digest', 'bearer', 'custom']
            if v not in valid_types:
                raise ValueError(f"Tipo de autenticación debe ser uno de: {', '.join(valid_types)}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "password": "new_secure_password",
                "description": "Credenciales actualizadas"
            }
        }


class TestCredentialRequest(BaseModel):
    """Request para probar credenciales."""
    
    username: str = Field(..., description="Nombre de usuario a probar")
    password: SecretStr = Field(..., description="Contraseña a probar")
    auth_type: str = Field("basic", description="Tipo de autenticación")
    test_url: Optional[str] = Field(None, description="URL específica para probar")
    
    @validator('username')
    def validate_username_field(cls, v):
        """Valida el nombre de usuario."""
        return validate_username(v)
    
    @validator('password')
    def validate_password_field(cls, v):
        """Valida la contraseña."""
        if v:
            validate_password(v.get_secret_value())
        return v
    
    @validator('test_url')
    def validate_test_url(cls, v):
        """Valida la URL de prueba si se proporciona."""
        if v is not None:
            # Validación básica de URL
            if not v.startswith(('http://', 'https://', 'rtsp://')):
                raise ValueError("URL debe comenzar con http://, https:// o rtsp://")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "test_user",
                "password": "test_password",
                "auth_type": "digest",
                "test_url": "http://192.168.1.100/api/auth"
            }
        }