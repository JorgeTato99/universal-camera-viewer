"""
Modelos base para respuestas de la API.

Este módulo proporciona clases genéricas reutilizables para
mantener consistencia en las respuestas de la API.
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# TypeVar para respuestas paginadas genéricas
T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Respuesta paginada genérica para cualquier tipo de dato.
    
    Esta clase base proporciona una estructura consistente para
    todas las respuestas paginadas en la API.
    
    Attributes:
        total: Número total de elementos disponibles
        page: Página actual (1-indexed)
        page_size: Tamaño de la página
        items: Lista de elementos de tipo T
        has_next: Si existe página siguiente
        has_previous: Si existe página anterior
        total_pages: Número total de páginas
    """
    total: int = Field(..., ge=0, description="Total de elementos disponibles")
    page: int = Field(..., ge=1, description="Página actual (1-indexed)")
    page_size: int = Field(..., ge=1, le=200, description="Tamaño de página")
    items: List[T] = Field(..., description="Lista de elementos")
    
    @property
    def has_next(self) -> bool:
        """Indica si hay página siguiente."""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Indica si hay página anterior."""
        return self.page > 1
    
    @property
    def total_pages(self) -> int:
        """Calcula el número total de páginas."""
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
    
    model_config = ConfigDict(
        # Permitir propiedades computadas en serialización
        extra='forbid',
        validate_assignment=True,
        # Para compatibilidad con modelos existentes
        from_attributes=True
    )
    
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override para incluir propiedades computadas."""
        data = super().model_dump(**kwargs)
        data['has_next'] = self.has_next
        data['has_previous'] = self.has_previous
        data['total_pages'] = self.total_pages
        return data


class TimestampedResponse(BaseModel):
    """
    Respuesta base con timestamp.
    
    Proporciona un timestamp consistente para respuestas
    que necesitan indicar cuándo fueron generadas.
    """
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento de generación de la respuesta (UTC)"
    )
    
    model_config = ConfigDict(
        from_attributes=True
    )


class ErrorDetail(BaseModel):
    """
    Detalle de error estructurado.
    
    Proporciona información detallada sobre errores
    de manera consistente en toda la API.
    """
    code: str = Field(..., description="Código único del error")
    message: str = Field(..., description="Mensaje descriptivo del error")
    field: Optional[str] = Field(None, description="Campo relacionado al error")
    details: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "El campo es requerido",
                "field": "camera_id",
                "details": {"expected_type": "string", "received": "null"}
            }
        }


class ErrorResponse(BaseModel):
    """
    Respuesta de error estándar.
    
    Estructura consistente para todos los errores de la API.
    """
    error: ErrorDetail = Field(..., description="Detalle del error")
    request_id: Optional[str] = Field(None, description="ID único de la petición")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento del error (UTC)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "CAMERA_NOT_FOUND",
                    "message": "La cámara especificada no existe",
                    "field": "camera_id",
                    "details": {"camera_id": "cam_123"}
                },
                "request_id": "req_abc123",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class SuccessResponse(BaseModel):
    """
    Respuesta de éxito genérica.
    
    Para operaciones que no retornan datos específicos.
    """
    success: bool = Field(True, description="Indica operación exitosa")
    message: str = Field(..., description="Mensaje descriptivo")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Momento de la operación (UTC)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operación completada exitosamente",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }


class BaseMetadata(BaseModel):
    """
    Modelo base para metadata estructurada.
    
    Proporciona campos comunes para metadata en diferentes contextos.
    Puede ser extendido para casos específicos.
    """
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha de creación"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Última actualización"
    )
    created_by: Optional[str] = Field(
        None,
        description="Usuario o sistema que creó el registro"
    )
    version: Optional[str] = Field(
        None,
        description="Versión del registro"
    )
    tags: Optional[List[str]] = Field(
        default_factory=list,
        description="Etiquetas asociadas"
    )
    
    model_config = ConfigDict(
        from_attributes=True
    )