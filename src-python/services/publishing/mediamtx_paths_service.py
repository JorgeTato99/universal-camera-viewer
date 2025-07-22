"""
Servicio para gestión de paths en MediaMTX.

Maneja la generación, validación y gestión de paths de publicación,
incluyendo plantillas, paths predefinidos y verificación de disponibilidad.
"""

import re
import uuid
import random
import string
import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
from pathlib import Path

from services.base_service import BaseService
from services.database.mediamtx_db_service import get_mediamtx_db_service
from services.publishing import MediaMTXClient
from utils.exceptions import ServiceError, ValidationError
from models.camera_model import CameraModel


logger = logging.getLogger(__name__)


@dataclass
class PathTemplate:
    """Plantilla predefinida para generación de paths."""
    template_id: str
    name: str
    pattern: str
    description: str
    example: str
    
    
# Plantillas predefinidas para paths
PREDEFINED_TEMPLATES = {
    "simple": PathTemplate(
        template_id="simple",
        name="Simple",
        pattern="{camera_code}",
        description="Solo el código de la cámara",
        example="cam_a1b2c3d4"
    ),
    "timestamped": PathTemplate(
        template_id="timestamped",
        name="Con marca de tiempo",
        pattern="{camera_code}_{timestamp}",
        description="Código de cámara con fecha y hora",
        example="cam_a1b2c3d4_20250122_143052"
    ),
    "instance_aware": PathTemplate(
        template_id="instance_aware",
        name="Con ID de instancia",
        pattern="{instance_id}_{camera_code}",
        description="ID de instancia UCV + código de cámara",
        example="ucv_abc123_cam_a1b2c3d4"
    ),
    "descriptive": PathTemplate(
        template_id="descriptive",
        name="Descriptivo",
        pattern="{camera_name}_{date}",
        description="Nombre de cámara con fecha",
        example="entrada_principal_20250122"
    ),
    "multi_instance": PathTemplate(
        template_id="multi_instance",
        name="Multi-instancia",
        pattern="{hostname}_{camera_name}",
        description="Hostname del servidor + nombre de cámara",
        example="servidor01_entrada_principal"
    ),
    "secure": PathTemplate(
        template_id="secure",
        name="Seguro",
        pattern="{camera_code}_{random}",
        description="Código de cámara con sufijo aleatorio",
        example="cam_a1b2c3d4_x7y9z2"
    )
}


class MediaMTXPathsService(BaseService):
    """
    Servicio para gestión de paths en MediaMTX.
    
    Responsabilidades:
    - Generar paths únicos basados en plantillas
    - Validar disponibilidad de paths
    - Gestionar paths predefinidos
    - Mantener registro histórico
    - Detectar y advertir sobre paths antiguos
    
    Attributes:
        _instance_id: UUID único de esta instancia de UCV
        _hostname: Nombre del host actual
        _db_service: Servicio de base de datos
        _mediamtx_client: Cliente de API MediaMTX
        _path_cache: Cache de paths activos
        _reserved_paths: Set de paths reservados
    """
    
    def __init__(self):
        """Inicializa el servicio de paths."""
        super().__init__()
        self._instance_id: Optional[str] = None
        self._hostname: Optional[str] = None
        self._db_service = None
        self._mediamtx_client: Optional[MediaMTXClient] = None
        self._path_cache: Dict[str, Dict[str, Any]] = {}
        self._reserved_paths: Set[str] = set()
        self._cache_lock = asyncio.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def initialize(self) -> None:
        """
        Inicializa el servicio y sus dependencias.
        
        - Genera o recupera el instance_id
        - Obtiene el hostname del sistema
        - Conecta con servicios necesarios
        """
        self.logger.info("Inicializando MediaMTXPathsService")
        
        try:
            # Generar o recuperar instance_id
            self._instance_id = await self._get_or_create_instance_id()
            self.logger.info(f"Instance ID: {self._instance_id}")
            
            # Obtener hostname
            import socket
            self._hostname = socket.gethostname()
            self.logger.debug(f"Hostname: {self._hostname}")
            
            # Inicializar servicios
            self._db_service = get_mediamtx_db_service()
            # TODO: MediaMTXClient necesita URL de API para inicializarse
            # Por ahora no inicializar, se debe pasar desde el presenter
            # self._mediamtx_client = MediaMTXClient(api_url)
            
            # Cargar paths reservados desde BD
            await self._load_reserved_paths()
            
            self.logger.info("MediaMTXPathsService inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando servicio: {e}")
            raise ServiceError(
                f"Error inicializando MediaMTXPathsService: {str(e)}",
                error_code="PATH_SERVICE_INIT_ERROR"
            )
    
    async def _get_or_create_instance_id(self) -> str:
        """
        Obtiene o crea el ID único de la instancia.
        
        TODO: Cuando se implemente persistencia de configuración,
        guardar este ID para mantenerlo entre reinicios.
        
        Returns:
            UUID v4 como string (sin guiones, 8 caracteres)
        """
        # TODO: Implementar persistencia del instance_id
        # Por ahora, generar uno nuevo cada vez
        instance_uuid = str(uuid.uuid4()).replace('-', '')[:8]
        return f"ucv_{instance_uuid}"
    
    async def _load_reserved_paths(self) -> None:
        """Carga los paths reservados/predefinidos desde la BD."""
        try:
            # TODO: Implementar query para cargar paths permanentes
            # desde la tabla mediamtx_paths
            self._reserved_paths.clear()
            
            # Por ahora, solo registrar algunos paths del sistema
            self._reserved_paths.update([
                "test", "demo", "default", "system"
            ])
            
        except Exception as e:
            self.logger.error(f"Error cargando paths reservados: {e}")
    
    def generate_path(
        self,
        camera: CameraModel,
        template: str = "{instance_id}_{camera_code}",
        counter: Optional[int] = None
    ) -> str:
        """
        Genera un path basado en la plantilla proporcionada.
        
        Variables soportadas:
        - {instance_id}: ID único de la instancia UCV
        - {hostname}: Nombre del host servidor
        - {camera_id}: ID completo de la cámara
        - {camera_code}: Código corto (primeros 8 chars)
        - {camera_name}: Nombre amigable (slug)
        - {timestamp}: YYYYMMDD_HHMMSS
        - {date}: YYYYMMDD
        - {random}: 6 caracteres aleatorios
        - {counter}: Contador incremental
        
        Args:
            camera: Modelo de la cámara
            template: Plantilla para generar el path
            counter: Contador opcional para paths numerados
            
        Returns:
            Path generado según la plantilla
        """
        # Preparar variables
        now = datetime.now()
        camera_code = camera.camera_id.split('-')[0][:8]
        camera_name = self._slugify(camera.name)
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Diccionario de reemplazos
        replacements = {
            'instance_id': self._instance_id or 'ucv',
            'hostname': self._hostname or 'localhost',
            'camera_id': camera.camera_id,
            'camera_code': camera_code,
            'camera_name': camera_name,
            'timestamp': now.strftime('%Y%m%d_%H%M%S'),
            'date': now.strftime('%Y%m%d'),
            'random': random_suffix,
            'counter': str(counter) if counter is not None else '1'
        }
        
        # Generar path
        path = template
        for key, value in replacements.items():
            path = path.replace(f'{{{key}}}', value)
            
        # Limpiar y validar
        path = self._sanitize_path(path)
        
        return path
    
    def _slugify(self, text: str) -> str:
        """
        Convierte texto a formato slug válido para paths.
        
        Args:
            text: Texto a convertir
            
        Returns:
            Texto en formato slug (minúsculas, sin espacios ni caracteres especiales)
        """
        # Convertir a minúsculas y reemplazar espacios
        slug = text.lower().strip()
        slug = re.sub(r'\s+', '_', slug)
        
        # Remover caracteres especiales
        slug = re.sub(r'[^a-z0-9_-]', '', slug)
        
        # Limitar longitud
        return slug[:32]
    
    def _sanitize_path(self, path: str) -> str:
        """
        Sanitiza un path para asegurar que sea válido.
        
        Args:
            path: Path a sanitizar
            
        Returns:
            Path sanitizado
        """
        # Remover caracteres no válidos
        path = re.sub(r'[^a-zA-Z0-9_-]', '', path)
        
        # Remover guiones bajos múltiples
        path = re.sub(r'_+', '_', path)
        
        # Remover guiones al inicio/final
        path = path.strip('_-')
        
        # Limitar longitud (MediaMTX típicamente soporta hasta 64 chars)
        return path[:50]
    
    async def check_availability(
        self,
        path: str,
        check_mediamtx: bool = True
    ) -> Dict[str, Any]:
        """
        Verifica la disponibilidad de un path.
        
        Args:
            path: Path a verificar
            check_mediamtx: Si verificar también en el servidor MediaMTX
            
        Returns:
            Dict con información de disponibilidad:
            {
                "available": bool,
                "path": str,
                "reason": str (si no está disponible),
                "suggestions": List[str] (alternativas si no está disponible)
            }
        """
        result = {
            "available": True,
            "path": path,
            "reason": None,
            "suggestions": []
        }
        
        # Verificar si es un path reservado
        if path in self._reserved_paths:
            result["available"] = False
            result["reason"] = "Path reservado del sistema"
            
        # Verificar en BD local
        if result["available"]:
            # TODO: Implementar verificación en BD
            # existing = await self._db_service.get_path_by_name(path)
            # if existing:
            #     result["available"] = False
            #     result["reason"] = "Path ya existe en la base de datos"
            pass
        
        # Verificar en MediaMTX si está configurado
        if result["available"] and check_mediamtx and self._mediamtx_client:
            try:
                paths = await self._mediamtx_client.list_paths()
                if any(p.name == path for p in paths):
                    result["available"] = False
                    result["reason"] = "Path actualmente en uso en MediaMTX"
            except Exception as e:
                self.logger.warning(f"No se pudo verificar en MediaMTX: {e}")
        
        # Generar sugerencias si no está disponible
        if not result["available"]:
            result["suggestions"] = self._generate_alternative_paths(path)
            
        return result
    
    def _generate_alternative_paths(self, base_path: str, count: int = 3) -> List[str]:
        """
        Genera paths alternativos basados en uno no disponible.
        
        Args:
            base_path: Path base
            count: Número de alternativas a generar
            
        Returns:
            Lista de paths alternativos
        """
        alternatives = []
        
        # Agregar timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        alternatives.append(f"{base_path}_{timestamp}")
        
        # Agregar sufijos numéricos
        for i in range(2, count + 2):
            alternatives.append(f"{base_path}_{i}")
            
        # Agregar sufijo aleatorio
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        alternatives.append(f"{base_path}_{random_suffix}")
        
        return alternatives[:count]
    
    async def create_predefined_path(
        self,
        path_name: str,
        camera_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea un path predefinido/permanente para una cámara.
        
        Args:
            path_name: Nombre del path
            camera_id: ID de la cámara
            config: Configuración adicional del path
            
        Returns:
            Información del path creado
        """
        # Validar disponibilidad
        availability = await self.check_availability(path_name)
        if not availability["available"]:
            raise ValidationError(
                f"Path '{path_name}' no está disponible: {availability['reason']}"
            )
        
        # TODO: Implementar creación en BD
        # path_data = await self._db_service.create_path({
        #     "path_name": path_name,
        #     "camera_id": camera_id,
        #     "is_permanent": True,
        #     **config
        # })
        
        # Por ahora, retornar mock
        path_data = {
            "path_id": str(uuid.uuid4()),
            "path_name": path_name,
            "camera_id": camera_id,
            "is_permanent": True,
            "created_at": datetime.now().isoformat()
        }
        
        # Agregar a paths reservados
        self._reserved_paths.add(path_name)
        
        return path_data
    
    async def get_suggested_path(
        self,
        camera: CameraModel,
        template_id: str = "instance_aware"
    ) -> str:
        """
        Obtiene un path sugerido disponible para una cámara.
        
        Args:
            camera: Modelo de la cámara
            template_id: ID de la plantilla a usar
            
        Returns:
            Path disponible sugerido
        """
        # Obtener plantilla
        template = PREDEFINED_TEMPLATES.get(
            template_id,
            PREDEFINED_TEMPLATES["instance_aware"]
        )
        
        # Generar path base
        base_path = self.generate_path(camera, template.pattern)
        
        # Verificar disponibilidad
        availability = await self.check_availability(base_path)
        
        if availability["available"]:
            return base_path
            
        # Si no está disponible, probar con contador
        for i in range(2, 10):
            path_with_counter = f"{base_path}_{i}"
            availability = await self.check_availability(path_with_counter)
            if availability["available"]:
                return path_with_counter
                
        # Si todo falla, agregar timestamp
        return f"{base_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def test_path(
        self,
        path_id: str,
        test_type: str = "availability"
    ) -> Dict[str, Any]:
        """
        Ejecuta pruebas sobre un path.
        
        Tipos de prueba:
        - availability: Verifica si el path está disponible
        - format: Valida el formato del path
        - connectivity: Prueba conexión con MediaMTX
        - publish: Intenta publicar temporalmente (5 segundos)
        
        Args:
            path_id: ID o nombre del path
            test_type: Tipo de prueba a ejecutar
            
        Returns:
            Resultados de la prueba
        """
        results = {
            "path_id": path_id,
            "test_type": test_type,
            "success": False,
            "message": "",
            "details": {}
        }
        
        try:
            if test_type == "availability":
                # Prueba de disponibilidad
                check = await self.check_availability(path_id)
                results["success"] = check["available"]
                results["message"] = "Path disponible" if check["available"] else check["reason"]
                results["details"] = check
                
            elif test_type == "format":
                # Validación de formato
                is_valid = self._validate_path_format(path_id)
                results["success"] = is_valid
                results["message"] = "Formato válido" if is_valid else "Formato inválido"
                results["details"]["sanitized"] = self._sanitize_path(path_id)
                
            elif test_type == "connectivity":
                # Prueba de conectividad con MediaMTX
                if self._mediamtx_client:
                    try:
                        await self._mediamtx_client.check_health()
                        results["success"] = True
                        results["message"] = "Conexión con MediaMTX exitosa"
                    except Exception as e:
                        results["success"] = False
                        results["message"] = f"Error de conexión: {str(e)}"
                else:
                    results["success"] = False
                    results["message"] = "Cliente MediaMTX no configurado"
                    
            elif test_type == "publish":
                # TODO: Implementar publicación temporal de prueba
                # Esto requeriría:
                # 1. Crear una fuente de video de prueba
                # 2. Publicar por 5 segundos
                # 3. Verificar que el path aparece en MediaMTX
                # 4. Detener y limpiar
                results["success"] = False
                results["message"] = "Prueba de publicación pendiente de implementación"
                results["details"]["note"] = "TODO: Implementar con FFmpeg test pattern"
                
            else:
                results["success"] = False
                results["message"] = f"Tipo de prueba '{test_type}' no reconocido"
                
        except Exception as e:
            results["success"] = False
            results["message"] = f"Error durante la prueba: {str(e)}"
            self.logger.error(f"Error en test_path: {e}")
            
        return results
    
    def _validate_path_format(self, path: str) -> bool:
        """
        Valida que un path tenga formato correcto.
        
        Args:
            path: Path a validar
            
        Returns:
            True si el formato es válido
        """
        # Debe tener entre 3 y 50 caracteres
        if len(path) < 3 or len(path) > 50:
            return False
            
        # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, path))
    
    async def get_old_paths_warnings(
        self,
        days_threshold: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtiene advertencias sobre paths antiguos no utilizados.
        
        NOTE: No elimina automáticamente, solo advierte al usuario.
        
        Args:
            days_threshold: Días de antigüedad para considerar un path como viejo
            
        Returns:
            Lista de advertencias sobre paths antiguos
        """
        warnings = []
        
        # TODO: Implementar query a BD para encontrar paths antiguos
        # Criterios:
        # 1. Paths en mediamtx_paths que no están en camera_publications
        # 2. Paths en publication_history más antiguos que threshold
        # 3. Paths sin actividad reciente
        
        # Mock data por ahora
        warnings.append({
            "path_name": "old_camera_123",
            "last_used": "2024-12-01T10:00:00",
            "days_inactive": 52,
            "suggestion": "Considere eliminar este path si ya no se utiliza"
        })
        
        return warnings
    
    async def get_path_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre el uso de paths.
        
        Returns:
            Estadísticas de uso de paths
        """
        stats = {
            "total_paths": len(self._reserved_paths),
            "active_paths": 0,  # TODO: Contar desde MediaMTX
            "predefined_paths": 0,  # TODO: Contar desde BD
            "dynamic_paths": 0,  # TODO: Contar desde BD
            "warnings": len(await self.get_old_paths_warnings()),
            "instance_id": self._instance_id,
            "hostname": self._hostname
        }
        
        return stats
    
    def get_templates(self) -> List[PathTemplate]:
        """
        Obtiene las plantillas predefinidas disponibles.
        
        Returns:
            Lista de plantillas disponibles
        """
        return list(PREDEFINED_TEMPLATES.values())
    
    async def cleanup(self) -> None:
        """Limpia recursos del servicio."""
        self.logger.info("Limpiando MediaMTXPathsService")
        self._path_cache.clear()
        self._reserved_paths.clear()


# Singleton del servicio
_paths_service: Optional[MediaMTXPathsService] = None


def get_mediamtx_paths_service() -> MediaMTXPathsService:
    """
    Obtiene la instancia singleton del servicio de paths.
    
    Returns:
        Instancia única del servicio
    """
    global _paths_service
    
    if _paths_service is None:
        _paths_service = MediaMTXPathsService()
        
    return _paths_service