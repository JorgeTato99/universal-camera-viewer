"""
Validadores para tests de integración.

Este módulo proporciona herramientas para validar respuestas
del backend contra tipos TypeScript del frontend.
"""

from .typescript_parser import TypeScriptParser
from .type_validator import TypeValidator

__all__ = ['TypeScriptParser', 'TypeValidator']