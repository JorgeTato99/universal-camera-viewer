"""
Procesador de frames para optimización y análisis.

Proporciona herramientas para procesar frames antes
de su conversión y envío.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any
import logging
from dataclasses import dataclass


@dataclass
class ProcessingOptions:
    """Opciones de procesamiento de frames."""
    resize: Optional[Tuple[int, int]] = None
    denoise: bool = False
    enhance_contrast: bool = False
    detect_motion: bool = False
    add_timestamp: bool = False
    add_overlay: bool = False
    overlay_text: str = ""


class FrameProcessor:
    """
    Procesador de frames con diversas opciones de optimización.
    
    Permite aplicar transformaciones y análisis a los frames
    antes de su conversión final.
    """
    
    def __init__(self):
        """Inicializa el procesador."""
        self.logger = logging.getLogger(__name__)
        
        # Para detección de movimiento
        self._last_frame: Optional[np.ndarray] = None
        self._motion_threshold = 0.01  # 1% de píxeles cambiados
    
    def process_frame(
        self,
        frame: np.ndarray,
        options: ProcessingOptions
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Procesa un frame según las opciones especificadas.
        
        Args:
            frame: Frame original
            options: Opciones de procesamiento
            
        Returns:
            Tupla (frame_procesado, metadata)
        """
        if frame is None or frame.size == 0:
            raise ValueError("Frame inválido")
        
        processed = frame.copy()
        metadata = {}
        
        # Aplicar procesamiento en orden
        if options.resize:
            processed = self._resize_frame(processed, options.resize)
            metadata['resized'] = True
            metadata['new_size'] = processed.shape[:2]
        
        if options.denoise:
            processed = self._denoise_frame(processed)
            metadata['denoised'] = True
        
        if options.enhance_contrast:
            processed = self._enhance_contrast(processed)
            metadata['contrast_enhanced'] = True
        
        if options.detect_motion:
            has_motion, motion_score = self._detect_motion(processed)
            metadata['has_motion'] = has_motion
            metadata['motion_score'] = motion_score
        
        if options.add_timestamp:
            processed = self._add_timestamp(processed)
            metadata['timestamp_added'] = True
        
        if options.add_overlay and options.overlay_text:
            processed = self._add_overlay(processed, options.overlay_text)
            metadata['overlay_added'] = True
        
        return processed, metadata
    
    def _resize_frame(self, frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        Redimensiona el frame manteniendo aspect ratio.
        
        Args:
            frame: Frame original
            target_size: (width, height) objetivo
            
        Returns:
            Frame redimensionado
        """
        h, w = frame.shape[:2]
        target_w, target_h = target_size
        
        # Calcular aspect ratio
        aspect = w / h
        
        # Calcular nuevo tamaño manteniendo aspect ratio
        if aspect > target_w / target_h:
            new_w = target_w
            new_h = int(target_w / aspect)
        else:
            new_h = target_h
            new_w = int(target_h * aspect)
        
        # Redimensionar
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Crear frame con padding si es necesario
        if new_w < target_w or new_h < target_h:
            padded = np.zeros((target_h, target_w, 3), dtype=frame.dtype)
            
            # Centrar frame redimensionado
            y_offset = (target_h - new_h) // 2
            x_offset = (target_w - new_w) // 2
            
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            return padded
        
        return resized
    
    def _denoise_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Aplica reducción de ruido al frame.
        
        Args:
            frame: Frame con ruido
            
        Returns:
            Frame con ruido reducido
        """
        # Aplicar filtro bilateral para reducir ruido preservando bordes
        denoised = cv2.bilateralFilter(frame, 9, 75, 75)
        return denoised
    
    def _enhance_contrast(self, frame: np.ndarray) -> np.ndarray:
        """
        Mejora el contraste del frame.
        
        Args:
            frame: Frame original
            
        Returns:
            Frame con contraste mejorado
        """
        # Convertir a LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Separar canales
        l, a, b = cv2.split(lab)
        
        # Aplicar CLAHE al canal L
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Recombinar canales
        enhanced_lab = cv2.merge([l, a, b])
        
        # Convertir de vuelta a BGR
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def _detect_motion(self, frame: np.ndarray) -> Tuple[bool, float]:
        """
        Detecta movimiento comparando con el frame anterior.
        
        Args:
            frame: Frame actual
            
        Returns:
            Tupla (hay_movimiento, score_movimiento)
        """
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self._last_frame is None:
            self._last_frame = gray
            return False, 0.0
        
        # Calcular diferencia absoluta
        frame_diff = cv2.absdiff(self._last_frame, gray)
        
        # Aplicar threshold
        _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
        
        # Calcular porcentaje de píxeles cambiados
        motion_pixels = cv2.countNonZero(thresh)
        total_pixels = frame.shape[0] * frame.shape[1]
        motion_score = motion_pixels / total_pixels
        
        # Actualizar frame anterior
        self._last_frame = gray
        
        # Determinar si hay movimiento significativo
        has_motion = motion_score > self._motion_threshold
        
        return has_motion, motion_score
    
    def _add_timestamp(self, frame: np.ndarray) -> np.ndarray:
        """
        Agrega timestamp al frame.
        
        Args:
            frame: Frame original
            
        Returns:
            Frame con timestamp
        """
        from datetime import datetime
        
        # Obtener timestamp actual
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Configurar texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        color = (255, 255, 255)  # Blanco
        
        # Calcular posición (esquina superior izquierda)
        position = (10, 25)
        
        # Agregar fondo negro para mejor legibilidad
        (text_width, text_height), _ = cv2.getTextSize(
            timestamp, font, font_scale, thickness
        )
        
        cv2.rectangle(
            frame,
            (position[0] - 5, position[1] - text_height - 5),
            (position[0] + text_width + 5, position[1] + 5),
            (0, 0, 0),
            -1
        )
        
        # Agregar texto
        cv2.putText(
            frame, timestamp, position, font,
            font_scale, color, thickness, cv2.LINE_AA
        )
        
        return frame
    
    def _add_overlay(self, frame: np.ndarray, text: str) -> np.ndarray:
        """
        Agrega texto overlay al frame.
        
        Args:
            frame: Frame original
            text: Texto a agregar
            
        Returns:
            Frame con overlay
        """
        # Configurar texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        color = (0, 255, 0)  # Verde
        
        # Calcular posición (centrado en la parte superior)
        (text_width, text_height), _ = cv2.getTextSize(
            text, font, font_scale, thickness
        )
        
        position = ((frame.shape[1] - text_width) // 2, 40)
        
        # Agregar fondo semi-transparente
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (position[0] - 10, position[1] - text_height - 10),
            (position[0] + text_width + 10, position[1] + 10),
            (0, 0, 0),
            -1
        )
        
        # Mezclar con transparencia
        alpha = 0.7
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        # Agregar texto
        cv2.putText(
            frame, text, position, font,
            font_scale, color, thickness, cv2.LINE_AA
        )
        
        return frame
    
    def reset_motion_detection(self) -> None:
        """Reinicia la detección de movimiento."""
        self._last_frame = None
        self.logger.debug("Detección de movimiento reiniciada")