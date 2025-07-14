"""
Modelo de dominio para frames de video.

Define la estructura de datos para un frame individual.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import numpy as np


@dataclass
class FrameMetadata:
    """
    Metadatos asociados a un frame de video.
    
    Attributes:
        timestamp: Momento de captura del frame
        frame_number: Número secuencial del frame
        original_size: Tamaño original (width, height)
        processed_size: Tamaño después de procesamiento
        encoding: Formato de codificación (jpeg, png, etc)
        quality: Calidad de compresión (1-100)
        processing_time_ms: Tiempo de procesamiento en ms
    """
    timestamp: datetime = field(default_factory=datetime.now)
    frame_number: int = 0
    original_size: Tuple[int, int] = (0, 0)
    processed_size: Optional[Tuple[int, int]] = None
    encoding: str = "jpeg"
    quality: int = 85
    processing_time_ms: float = 0.0
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if self.quality < 1 or self.quality > 100:
            raise ValueError(f"quality debe estar entre 1 y 100, recibido: {self.quality}")


@dataclass
class FrameModel:
    """
    Modelo que representa un frame de video individual.
    
    Attributes:
        camera_id: ID de la cámara que generó el frame
        stream_id: ID del stream al que pertenece
        data: Datos del frame (numpy array o bytes)
        metadata: Metadatos del frame
        is_keyframe: Si es un keyframe
        error: Mensaje de error si hubo problemas
    """
    
    # Identificadores
    camera_id: str
    stream_id: str
    
    # Datos del frame
    data: Optional[Any] = None  # numpy.ndarray o bytes
    
    # Metadatos
    metadata: FrameMetadata = field(default_factory=FrameMetadata)
    
    # Propiedades del frame
    is_keyframe: bool = False
    has_motion: bool = False
    
    # Error handling
    error: Optional[str] = None
    
    def __post_init__(self):
        """Validación después de inicialización."""
        self.validate()
    
    def validate(self) -> None:
        """Valida la integridad del modelo."""
        if not self.camera_id:
            raise ValueError("camera_id es obligatorio")
        if not self.stream_id:
            raise ValueError("stream_id es obligatorio")
    
    def is_valid(self) -> bool:
        """Verifica si el frame tiene datos válidos."""
        return self.data is not None and self.error is None
    
    def get_size(self) -> Tuple[int, int]:
        """Obtiene el tamaño del frame."""
        if self.metadata.processed_size:
            return self.metadata.processed_size
        return self.metadata.original_size
    
    def get_data_size_bytes(self) -> int:
        """Calcula el tamaño de los datos en bytes."""
        if self.data is None:
            return 0
        
        if isinstance(self.data, np.ndarray):
            return self.data.nbytes
        elif isinstance(self.data, bytes):
            return len(self.data)
        elif isinstance(self.data, str):
            # Base64 string
            return len(self.data.encode('utf-8'))
        
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el modelo a diccionario.
        
        Nota: No incluye los datos del frame para evitar problemas de serialización.
        """
        return {
            'camera_id': self.camera_id,
            'stream_id': self.stream_id,
            'metadata': {
                'timestamp': self.metadata.timestamp.isoformat(),
                'frame_number': self.metadata.frame_number,
                'original_size': self.metadata.original_size,
                'processed_size': self.metadata.processed_size,
                'encoding': self.metadata.encoding,
                'quality': self.metadata.quality,
                'processing_time_ms': self.metadata.processing_time_ms
            },
            'is_keyframe': self.is_keyframe,
            'has_motion': self.has_motion,
            'has_data': self.data is not None,
            'data_size_bytes': self.get_data_size_bytes(),
            'error': self.error
        }
    
    @classmethod
    def create_error_frame(cls, camera_id: str, stream_id: str, error: str) -> 'FrameModel':
        """Crea un frame de error."""
        return cls(
            camera_id=camera_id,
            stream_id=stream_id,
            data=None,
            error=error
        )