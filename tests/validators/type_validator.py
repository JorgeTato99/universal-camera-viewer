"""
Validador de tipos TypeScript para respuestas del backend.

Este módulo valida que las respuestas del backend cumplan con las
interfaces TypeScript definidas en el frontend, asegurando consistencia
entre ambos sistemas.
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
from datetime import datetime

try:
    from .typescript_parser import TypeScriptParser
except ImportError:
    # Para ejecución directa del módulo
    from typescript_parser import TypeScriptParser


class ValidationError(Exception):
    """Error de validación de tipos."""
    
    def __init__(self, message: str, path: str = "", expected: Any = None, actual: Any = None):
        self.message = message
        self.path = path
        self.expected = expected
        self.actual = actual
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formatea el mensaje de error con contexto."""
        msg = f"Validation error"
        if self.path:
            msg += f" at '{self.path}'"
        msg += f": {self.message}"
        
        if self.expected is not None:
            msg += f"\n  Expected: {self.expected}"
        if self.actual is not None:
            msg += f"\n  Actual: {self.actual}"
            
        return msg


class TypeValidator:
    """
    Validador de respuestas contra tipos TypeScript.
    
    Valida que las respuestas del backend cumplan con las interfaces
    definidas en el frontend, detectando inconsistencias de tipos.
    """
    
    def __init__(self, ts_file_path: str):
        """
        Inicializa el validador con un archivo TypeScript.
        
        Args:
            ts_file_path: Ruta al archivo con definiciones TypeScript
        """
        self.parser = TypeScriptParser()
        self.interfaces = self.parser.parse_file(ts_file_path)
        
        # Mapeo de tipos TypeScript a validadores Python
        self.type_validators = {
            'string': self._validate_string,
            'number': self._validate_number,
            'boolean': self._validate_boolean,
            'any': lambda v, p: True  # any acepta todo
        }
    
    def validate_response(self, response: Dict[str, Any], interface_name: str) -> bool:
        """
        Valida una respuesta contra una interface TypeScript.
        
        Args:
            response: Respuesta del backend a validar
            interface_name: Nombre de la interface TypeScript
            
        Returns:
            True si la validación es exitosa
            
        Raises:
            ValidationError: Si la validación falla
            ValueError: Si la interface no existe
        """
        interface = self.parser.get_interface(interface_name)
        if not interface:
            raise ValueError(f"Interface '{interface_name}' no encontrada")
        
        if interface['type'] == 'enum':
            return self._validate_enum(response, interface['values'], interface_name)
        
        # Validar que sea un objeto
        if not isinstance(response, dict):
            raise ValidationError(
                "Se esperaba un objeto",
                interface_name,
                expected="object",
                actual=type(response).__name__
            )
        
        # Validar campos
        fields = interface['fields']
        
        # Verificar campos requeridos
        for field_name, field_info in fields.items():
            if not field_info['optional'] and field_name not in response:
                raise ValidationError(
                    f"Campo requerido '{field_name}' faltante",
                    f"{interface_name}.{field_name}"
                )
        
        # Validar cada campo presente
        for field_name, value in response.items():
            if field_name in fields:
                field_info = fields[field_name]
                self._validate_field(
                    value,
                    field_info['type'],
                    f"{interface_name}.{field_name}"
                )
            # TODO: Considerar si queremos ser estrictos con campos extra
            # Por ahora, permitimos campos adicionales
        
        return True
    
    def _validate_field(self, value: Any, type_info: Dict[str, Any], path: str) -> bool:
        """
        Valida un campo individual.
        
        Args:
            value: Valor a validar
            type_info: Información del tipo esperado
            path: Ruta del campo para mensajes de error
            
        Returns:
            True si es válido
            
        Raises:
            ValidationError: Si la validación falla
        """
        # Manejar None para campos opcionales
        if value is None:
            # TODO: Verificar si el campo es opcional en el contexto
            return True
        
        kind = type_info['kind']
        
        if kind == 'basic':
            return self._validate_basic_type(value, type_info['type'], path)
        
        elif kind == 'array':
            return self._validate_array(value, type_info['element'], path)
        
        elif kind == 'union':
            return self._validate_union(value, type_info['types'], path)
        
        elif kind == 'reference':
            # Validar contra otra interface o enum
            ref_name = type_info['type']
            ref_interface = self.parser.get_interface(ref_name)
            
            if ref_interface:
                if ref_interface['type'] == 'enum':
                    return self._validate_enum(value, ref_interface['values'], path)
                else:
                    # Validar recursivamente
                    return self.validate_response(value, ref_name)
            else:
                # Interface no encontrada, asumir válido
                # TODO: Log warning
                return True
        
        return True
    
    def _validate_basic_type(self, value: Any, expected_type: str, path: str) -> bool:
        """
        Valida tipos básicos.
        
        Args:
            value: Valor a validar
            expected_type: Tipo esperado ('string', 'number', 'boolean')
            path: Ruta para errores
            
        Returns:
            True si es válido
            
        Raises:
            ValidationError: Si el tipo no coincide
        """
        validator = self.type_validators.get(expected_type)
        if validator:
            return validator(value, path)
        
        # Tipo desconocido
        return True
    
    def _validate_string(self, value: Any, path: str) -> bool:
        """Valida que el valor sea string."""
        if not isinstance(value, str):
            raise ValidationError(
                "Se esperaba string",
                path,
                expected="string",
                actual=type(value).__name__
            )
        return True
    
    def _validate_number(self, value: Any, path: str) -> bool:
        """Valida que el valor sea número."""
        if not isinstance(value, (int, float)):
            raise ValidationError(
                "Se esperaba number",
                path,
                expected="number",
                actual=type(value).__name__
            )
        return True
    
    def _validate_boolean(self, value: Any, path: str) -> bool:
        """Valida que el valor sea booleano."""
        if not isinstance(value, bool):
            raise ValidationError(
                "Se esperaba boolean",
                path,
                expected="boolean",
                actual=type(value).__name__
            )
        return True
    
    def _validate_array(self, value: Any, element_type: Dict[str, Any], path: str) -> bool:
        """
        Valida un array y sus elementos.
        
        Args:
            value: Valor a validar
            element_type: Tipo de los elementos
            path: Ruta para errores
            
        Returns:
            True si es válido
        """
        if not isinstance(value, list):
            raise ValidationError(
                "Se esperaba array",
                path,
                expected="array",
                actual=type(value).__name__
            )
        
        # Validar cada elemento
        for i, element in enumerate(value):
            self._validate_field(element, element_type, f"{path}[{i}]")
        
        return True
    
    def _validate_union(self, value: Any, types: List[str], path: str) -> bool:
        """
        Valida un union type (tipo1 | tipo2 | ...).
        
        Args:
            value: Valor a validar
            types: Lista de tipos posibles
            path: Ruta para errores
            
        Returns:
            True si coincide con algún tipo
        """
        # Para strings literales en unions
        if isinstance(value, str) and value in types:
            return True
        
        # TODO: Manejar unions más complejos
        # Por ahora, aceptar si es string y está en la lista
        if not isinstance(value, str) or value not in types:
            raise ValidationError(
                f"Se esperaba uno de: {', '.join(types)}",
                path,
                expected=types,
                actual=value
            )
        
        return True
    
    def _validate_enum(self, value: Any, enum_values: List[str], path: str) -> bool:
        """
        Valida un valor de enum.
        
        Args:
            value: Valor a validar
            enum_values: Valores válidos del enum
            path: Ruta para errores
            
        Returns:
            True si es válido
        """
        if value not in enum_values:
            raise ValidationError(
                f"Valor de enum inválido",
                path,
                expected=enum_values,
                actual=value
            )
        return True
    
    def check_field_compatibility(
        self,
        backend_response: Dict[str, Any],
        interface_name: str,
        field_mappings: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Verifica compatibilidad de campos entre backend y frontend.
        
        Útil para detectar diferencias en nombres de campos como
        'id' vs 'path_id'.
        
        Args:
            backend_response: Respuesta del backend
            interface_name: Nombre de la interface TypeScript
            field_mappings: Mapeo opcional de campos backend -> frontend
            
        Returns:
            Lista de problemas encontrados
        """
        problems = []
        field_mappings = field_mappings or {}
        
        interface = self.parser.get_interface(interface_name)
        if not interface or interface['type'] != 'interface':
            return [f"Interface '{interface_name}' no encontrada o no es válida"]
        
        fields = interface['fields']
        
        # Verificar campos del frontend que faltan en backend
        for frontend_field, field_info in fields.items():
            backend_field = field_mappings.get(frontend_field, frontend_field)
            
            if backend_field not in backend_response and not field_info['optional']:
                problems.append(
                    f"Campo requerido '{frontend_field}' no encontrado en respuesta del backend"
                    f" (buscando como '{backend_field}')"
                )
        
        # Verificar campos del backend que no existen en frontend
        for backend_field in backend_response:
            # Buscar si este campo mapea a algo en el frontend
            frontend_field = None
            for ff, bf in field_mappings.items():
                if bf == backend_field:
                    frontend_field = ff
                    break
            
            if not frontend_field:
                frontend_field = backend_field
            
            if frontend_field not in fields:
                problems.append(
                    f"Campo '{backend_field}' del backend no existe en interface del frontend"
                )
        
        return problems
    
    def generate_mock_data(self, interface_name: str) -> Dict[str, Any]:
        """
        Genera datos mock que cumplen con una interface.
        
        Útil para testing cuando no se tienen datos reales.
        
        Args:
            interface_name: Nombre de la interface
            
        Returns:
            Objeto mock que cumple con la interface
            
        TODO: Esta es una implementación básica. Para producción,
        considerar usar librerías como faker para datos más realistas.
        """
        interface = self.parser.get_interface(interface_name)
        if not interface:
            raise ValueError(f"Interface '{interface_name}' no encontrada")
        
        if interface['type'] == 'enum':
            # Retornar el primer valor del enum
            return interface['values'][0] if interface['values'] else None
        
        mock_data = {}
        
        for field_name, field_info in interface['fields'].items():
            if not field_info['optional']:
                mock_data[field_name] = self._generate_mock_value(field_info['type'])
        
        return mock_data
    
    def _generate_mock_value(self, type_info: Dict[str, Any]) -> Any:
        """
        Genera un valor mock para un tipo.
        
        Args:
            type_info: Información del tipo
            
        Returns:
            Valor mock
        """
        kind = type_info['kind']
        
        if kind == 'basic':
            type_name = type_info['type']
            if type_name == 'string':
                return 'test_string'
            elif type_name == 'number':
                return 42
            elif type_name == 'boolean':
                return True
            else:
                return None
        
        elif kind == 'array':
            # Array vacío por defecto
            return []
        
        elif kind == 'union':
            # Primer valor del union
            return type_info['types'][0] if type_info['types'] else None
        
        elif kind == 'reference':
            # Intentar generar mock de la referencia
            ref_name = type_info['type']
            try:
                return self.generate_mock_data(ref_name)
            except:
                return {}
        
        return None