"""
Parser de tipos TypeScript para generar validadores.

Este módulo extrae interfaces desde archivos TypeScript y las convierte
en estructuras que pueden ser validadas contra respuestas del backend.

NOTA: Este es un parser simplificado que maneja las estructuras básicas
del archivo src/features/publishing/types.ts. Para un parser completo,
considerar usar una librería como ts-morph o el AST de TypeScript.
"""

import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json


class TypeScriptParser:
    """
    Parser simplificado de archivos TypeScript.
    
    Limitaciones actuales:
    - Solo parsea interfaces (no types, clases, etc.)
    - No maneja herencia de interfaces
    - No procesa genéricos complejos
    - Asume formato de código consistente
    
    TODO: Para producción, considerar usar una librería de parsing TypeScript
    como ts-morph o acceder al AST directamente.
    """
    
    def __init__(self):
        """Inicializa el parser."""
        self.interfaces: Dict[str, Dict[str, Any]] = {}
        
    def parse_file(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Parsea un archivo TypeScript y extrae las interfaces.
        
        Args:
            file_path: Ruta al archivo TypeScript
            
        Returns:
            Diccionario con interfaces parseadas
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
        content = path.read_text(encoding='utf-8')
        
        # Limpiar comentarios
        content = self._remove_comments(content)
        
        # Parsear interfaces
        self.interfaces = self._parse_interfaces(content)
        
        # Parsear enums
        enums = self._parse_enums(content)
        self.interfaces.update(enums)
        
        return self.interfaces
    
    def _remove_comments(self, content: str) -> str:
        """
        Elimina comentarios del código TypeScript.
        
        Args:
            content: Contenido del archivo
            
        Returns:
            Contenido sin comentarios
        """
        # Eliminar comentarios de línea
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        
        # Eliminar comentarios de bloque
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        return content
    
    def _parse_interfaces(self, content: str) -> Dict[str, Dict[str, Any]]:
        """
        Parsea interfaces TypeScript.
        
        Args:
            content: Contenido sin comentarios
            
        Returns:
            Diccionario de interfaces parseadas
        """
        interfaces = {}
        
        # Regex para encontrar interfaces
        interface_pattern = r'export\s+interface\s+(\w+)\s*\{([^}]+)\}'
        
        for match in re.finditer(interface_pattern, content, re.DOTALL):
            interface_name = match.group(1)
            interface_body = match.group(2)
            
            # Parsear campos de la interface
            fields = self._parse_interface_fields(interface_body)
            
            interfaces[interface_name] = {
                'type': 'interface',
                'fields': fields
            }
        
        return interfaces
    
    def _parse_interface_fields(self, body: str) -> Dict[str, Dict[str, Any]]:
        """
        Parsea los campos de una interface.
        
        Args:
            body: Cuerpo de la interface
            
        Returns:
            Diccionario de campos
        """
        fields = {}
        
        # Regex para campos de interface
        # Captura: nombre, opcional?, tipo
        field_pattern = r'(\w+)(\?)?:\s*([^;]+);'
        
        for match in re.finditer(field_pattern, body):
            field_name = match.group(1)
            is_optional = bool(match.group(2))
            field_type = match.group(3).strip()
            
            # Parsear el tipo
            parsed_type = self._parse_type(field_type)
            
            fields[field_name] = {
                'optional': is_optional,
                'type': parsed_type
            }
        
        return fields
    
    def _parse_type(self, type_str: str) -> Dict[str, Any]:
        """
        Parsea una expresión de tipo TypeScript.
        
        Args:
            type_str: String del tipo
            
        Returns:
            Diccionario representando el tipo
        """
        type_str = type_str.strip()
        
        # Tipos básicos
        basic_types = ['string', 'number', 'boolean', 'any']
        if type_str in basic_types:
            return {'kind': 'basic', 'type': type_str}
        
        # Arrays
        if type_str.endswith('[]'):
            element_type = type_str[:-2].strip()
            return {
                'kind': 'array',
                'element': self._parse_type(element_type)
            }
        
        # Union types (simplificado)
        if '|' in type_str:
            types = [t.strip().strip("'\"") for t in type_str.split('|')]
            return {
                'kind': 'union',
                'types': types
            }
        
        # Asumir que es una referencia a otra interface
        return {'kind': 'reference', 'type': type_str}
    
    def _parse_enums(self, content: str) -> Dict[str, Dict[str, Any]]:
        """
        Parsea enums TypeScript.
        
        Args:
            content: Contenido sin comentarios
            
        Returns:
            Diccionario de enums parseados
        """
        enums = {}
        
        # Regex para encontrar enums
        enum_pattern = r'export\s+enum\s+(\w+)\s*\{([^}]+)\}'
        
        for match in re.finditer(enum_pattern, content, re.DOTALL):
            enum_name = match.group(1)
            enum_body = match.group(2)
            
            # Parsear valores del enum
            values = self._parse_enum_values(enum_body)
            
            enums[enum_name] = {
                'type': 'enum',
                'values': values
            }
        
        return enums
    
    def _parse_enum_values(self, body: str) -> List[str]:
        """
        Parsea los valores de un enum.
        
        Args:
            body: Cuerpo del enum
            
        Returns:
            Lista de valores
        """
        values = []
        
        # Regex para valores de enum
        value_pattern = r'(\w+)\s*=\s*[\'"]([^\'",]+)[\'"]'
        
        for match in re.finditer(value_pattern, body):
            value = match.group(2)
            values.append(value)
        
        return values
    
    def get_interface(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene una interface parseada por nombre.
        
        Args:
            name: Nombre de la interface
            
        Returns:
            Interface parseada o None si no existe
        """
        return self.interfaces.get(name)
    
    def export_schema(self, interface_name: str) -> Dict[str, Any]:
        """
        Exporta una interface como schema JSON-like para validación.
        
        Args:
            interface_name: Nombre de la interface
            
        Returns:
            Schema para validación
            
        TODO: Este método genera un schema simplificado. Para producción,
        considerar generar JSON Schema completo.
        """
        interface = self.get_interface(interface_name)
        if not interface:
            raise ValueError(f"Interface '{interface_name}' no encontrada")
        
        if interface['type'] == 'enum':
            return {
                'type': 'enum',
                'values': interface['values']
            }
        
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        for field_name, field_info in interface['fields'].items():
            schema['properties'][field_name] = self._type_to_schema(field_info['type'])
            
            if not field_info['optional']:
                schema['required'].append(field_name)
        
        return schema
    
    def _type_to_schema(self, type_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convierte información de tipo a schema de validación.
        
        Args:
            type_info: Información del tipo
            
        Returns:
            Schema para el tipo
        """
        kind = type_info['kind']
        
        if kind == 'basic':
            type_map = {
                'string': 'string',
                'number': 'number',
                'boolean': 'boolean',
                'any': 'any'
            }
            return {'type': type_map.get(type_info['type'], 'any')}
        
        elif kind == 'array':
            return {
                'type': 'array',
                'items': self._type_to_schema(type_info['element'])
            }
        
        elif kind == 'union':
            return {
                'type': 'union',
                'values': type_info['types']
            }
        
        elif kind == 'reference':
            # Para referencias, intentar resolver
            ref_interface = self.get_interface(type_info['type'])
            if ref_interface and ref_interface['type'] == 'enum':
                return {
                    'type': 'enum',
                    'values': ref_interface['values']
                }
            else:
                # Por defecto, asumir objeto
                return {'type': 'object', 'reference': type_info['type']}
        
        return {'type': 'any'}