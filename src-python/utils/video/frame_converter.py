"""
Convertidor de frames con patrón Strategy.

Proporciona diferentes estrategias de conversión de frames OpenCV
a formatos compatibles con Flet UI.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import numpy as np
import cv2
import base64
from io import BytesIO
import logging


class FrameConversionStrategy(ABC):
    """Estrategia base para conversión de frames."""
    
    @abstractmethod
    def convert(self, frame: np.ndarray, quality: int = 85) -> any:
        """
        Convierte un frame a un formato específico.
        
        Args:
            frame: Frame OpenCV (numpy array)
            quality: Calidad de compresión (1-100)
            
        Returns:
            Frame convertido en el formato objetivo
        """
        pass
    
    @abstractmethod
    def get_mime_type(self) -> str:
        """Retorna el tipo MIME del formato de salida."""
        pass


class Base64JPEGStrategy(FrameConversionStrategy):
    """Convierte frames a JPEG codificado en base64."""
    
    def convert(self, frame: np.ndarray, quality: int = 85) -> str:
        """
        Convierte frame a JPEG base64.
        
        Args:
            frame: Frame BGR de OpenCV
            quality: Calidad JPEG (1-100)
            
        Returns:
            String base64 del JPEG
        """
        try:
            # OpenCV captura en BGR, cv2.imencode espera BGR para JPEG
            # No convertir a RGB ya que causaría inversión de colores
            
            # Codificar a JPEG directamente desde BGR
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            # Convertir a base64
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            
            return jpg_as_text
            
        except Exception as e:
            logging.error(f"Error convirtiendo frame a JPEG base64: {e}")
            raise
    
    def get_mime_type(self) -> str:
        return "image/jpeg"


class Base64PNGStrategy(FrameConversionStrategy):
    """Convierte frames a PNG codificado en base64."""
    
    def convert(self, frame: np.ndarray, quality: int = 85) -> str:
        """
        Convierte frame a PNG base64.
        
        Args:
            frame: Frame BGR de OpenCV
            quality: Nivel de compresión PNG (0-9, donde 9 es máxima compresión)
            
        Returns:
            String base64 del PNG
        """
        try:
            # OpenCV captura en BGR, cv2.imencode espera BGR para PNG
            # No convertir a RGB ya que causaría inversión de colores
            
            # Mapear quality (1-100) a compression level (0-9)
            compression_level = int(9 - (quality / 100 * 9))
            
            # Codificar a PNG directamente desde BGR
            encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), compression_level]
            _, buffer = cv2.imencode('.png', frame, encode_param)
            
            # Convertir a base64
            png_as_text = base64.b64encode(buffer).decode('utf-8')
            
            return png_as_text
            
        except Exception as e:
            logging.error(f"Error convirtiendo frame a PNG base64: {e}")
            raise
    
    def get_mime_type(self) -> str:
        return "image/png"


class BytesJPEGStrategy(FrameConversionStrategy):
    """Convierte frames a bytes JPEG."""
    
    def convert(self, frame: np.ndarray, quality: int = 85) -> bytes:
        """
        Convierte frame a bytes JPEG.
        
        Args:
            frame: Frame BGR de OpenCV
            quality: Calidad JPEG (1-100)
            
        Returns:
            Bytes del JPEG
        """
        try:
            # OpenCV captura en BGR, cv2.imencode espera BGR para JPEG
            # No convertir a RGB ya que causaría inversión de colores
            
            # Codificar a JPEG directamente desde BGR
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, buffer = cv2.imencode('.jpg', frame, encode_param)
            
            return buffer.tobytes()
            
        except Exception as e:
            logging.error(f"Error convirtiendo frame a bytes JPEG: {e}")
            raise
    
    def get_mime_type(self) -> str:
        return "image/jpeg"


class FrameConverter:
    """
    Convertidor de frames con soporte para múltiples estrategias.
    
    Attributes:
        strategy: Estrategia de conversión actual
        default_quality: Calidad por defecto para compresión
    """
    
    def __init__(self, strategy: Optional[FrameConversionStrategy] = None, default_quality: int = 85):
        """
        Inicializa el convertidor.
        
        Args:
            strategy: Estrategia de conversión (por defecto Base64JPEGStrategy)
            default_quality: Calidad por defecto (1-100)
        """
        self._strategy = strategy or Base64JPEGStrategy()
        self.default_quality = default_quality
        self.logger = logging.getLogger(__name__)
    
    def set_strategy(self, strategy: FrameConversionStrategy) -> None:
        """Cambia la estrategia de conversión."""
        self._strategy = strategy
    
    def convert_frame(
        self, 
        frame: np.ndarray, 
        resize: Optional[Tuple[int, int]] = None,
        quality: Optional[int] = None
    ) -> any:
        """
        Convierte un frame usando la estrategia actual.
        
        Args:
            frame: Frame OpenCV (numpy array)
            resize: Tupla (width, height) para redimensionar
            quality: Calidad de compresión (usa default si es None)
            
        Returns:
            Frame convertido según la estrategia
        """
        if frame is None or frame.size == 0:
            raise ValueError("Frame inválido o vacío")
        
        # Redimensionar si es necesario
        if resize:
            frame = self._resize_frame(frame, resize)
        
        # Usar calidad por defecto si no se especifica
        quality = quality or self.default_quality
        
        # Convertir usando la estrategia
        return self._strategy.convert(frame, quality)
    
    def convert_to_data_uri(
        self,
        frame: np.ndarray,
        resize: Optional[Tuple[int, int]] = None,
        quality: Optional[int] = None
    ) -> str:
        """
        Convierte un frame a Data URI para usar directamente en HTML/Flet.
        
        Args:
            frame: Frame OpenCV
            resize: Redimensionar a (width, height)
            quality: Calidad de compresión
            
        Returns:
            Data URI string: "data:image/jpeg;base64,..."
        """
        # Asegurar que usamos una estrategia base64
        original_strategy = self._strategy
        if not isinstance(self._strategy, (Base64JPEGStrategy, Base64PNGStrategy)):
            self._strategy = Base64JPEGStrategy()
        
        try:
            base64_data = self.convert_frame(frame, resize, quality)
            mime_type = self._strategy.get_mime_type()
            return f"data:{mime_type};base64,{base64_data}"
            
        finally:
            self._strategy = original_strategy
    
    def _resize_frame(self, frame: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
        """
        Redimensiona un frame manteniendo aspect ratio.
        
        Args:
            frame: Frame original
            size: (width, height) objetivo
            
        Returns:
            Frame redimensionado
        """
        h, w = frame.shape[:2]
        target_w, target_h = size
        
        # Calcular aspect ratio
        aspect = w / h
        
        # Calcular nuevo tamaño manteniendo aspect ratio
        if aspect > target_w / target_h:
            # Limitar por ancho
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            # Limitar por alto
            new_h = target_h
            new_w = int(target_h * aspect)
        
        # Redimensionar
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        self.logger.debug(f"Frame redimensionado de {w}x{h} a {new_w}x{new_h}")
        
        return resized
    
    @staticmethod
    def estimate_size(frame: np.ndarray, strategy: FrameConversionStrategy, quality: int = 85) -> int:
        """
        Estima el tamaño en bytes del frame convertido.
        
        Args:
            frame: Frame a convertir
            strategy: Estrategia de conversión
            quality: Calidad de compresión
            
        Returns:
            Tamaño estimado en bytes
        """
        converter = FrameConverter(strategy)
        result = converter.convert_frame(frame, quality=quality)
        
        if isinstance(result, str):
            # Base64 string
            return len(result.encode('utf-8'))
        elif isinstance(result, bytes):
            return len(result)
        else:
            return 0