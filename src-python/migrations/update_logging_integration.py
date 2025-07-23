#!/usr/bin/env python3
"""
Script para actualizar la integración del sistema de logging seguro.

Este script:
1. Identifica servicios que usan logging estándar
2. Los actualiza para usar el logging seguro
3. Aplica las mejores prácticas de sanitización
4. Genera un reporte de cambios
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import shutil
from datetime import datetime

# Agregar src-python al path
sys.path.insert(0, str(Path(__file__).parent.parent))


class LoggingIntegrationUpdater:
    """Actualiza servicios para usar el sistema de logging seguro."""
    
    def __init__(self, dry_run: bool = True):
        """
        Inicializa el actualizador.
        
        Args:
            dry_run: Si True, solo muestra cambios sin aplicarlos
        """
        self.dry_run = dry_run
        self.src_path = Path(__file__).parent.parent
        self.services_path = self.src_path / "services"
        self.changes: List[Dict[str, any]] = []
        
        # Patrones para detectar uso de logging
        self.import_patterns = [
            re.compile(r'^import logging$', re.MULTILINE),
            re.compile(r'^from logging import (.+)$', re.MULTILINE),
            re.compile(r'^import logging\.(.+)$', re.MULTILINE),
        ]
        
        # Patrón para detectar creación de logger
        self.logger_pattern = re.compile(
            r'(?:self\.)?logger\s*=\s*logging\.getLogger\(["\']?([\w\.]+)?["\']?\)',
            re.MULTILINE
        )
        
        # Servicios a excluir (ya usan logging seguro o son especiales)
        self.exclude_services = {
            'logging_service.py',  # El servicio mismo
            'base_service.py',     # Clase base, necesita tratamiento especial
            '__pycache__',
            '__init__.py'
        }
        
    def find_services_to_update(self) -> List[Path]:
        """
        Encuentra servicios que necesitan actualización.
        
        Returns:
            Lista de archivos que usan logging estándar
        """
        services_to_update = []
        
        for py_file in self.services_path.rglob("*.py"):
            # Saltar excluidos
            if any(exclude in str(py_file) for exclude in self.exclude_services):
                continue
                
            # Verificar si usa logging estándar
            content = py_file.read_text(encoding='utf-8')
            
            # Buscar imports de logging
            has_standard_logging = any(
                pattern.search(content) for pattern in self.import_patterns
            )
            
            # Verificar si ya usa logging seguro
            uses_secure_logging = (
                'from services.logging_service import get_secure_logger' in content or
                'from logging_service import get_secure_logger' in content
            )
            
            if has_standard_logging and not uses_secure_logging:
                services_to_update.append(py_file)
                
        return services_to_update
        
    def analyze_file(self, file_path: Path) -> Dict[str, any]:
        """
        Analiza un archivo para determinar cambios necesarios.
        
        Args:
            file_path: Ruta del archivo a analizar
            
        Returns:
            Diccionario con información del análisis
        """
        content = file_path.read_text(encoding='utf-8')
        
        analysis = {
            'file': file_path,
            'imports_to_update': [],
            'logger_creations': [],
            'sensitive_logs': [],
            'requires_sanitization': False
        }
        
        # Encontrar imports de logging
        for pattern in self.import_patterns:
            matches = pattern.findall(content)
            if matches:
                analysis['imports_to_update'].extend(matches)
                
        # Encontrar creaciones de logger
        logger_matches = self.logger_pattern.findall(content)
        analysis['logger_creations'] = logger_matches
        
        # Buscar logs que podrían contener información sensible
        sensitive_patterns = [
            (r'logger\.\w+\(.*password.*\)', 'password en log'),
            (r'logger\.\w+\(.*rtsp://.*@.*\)', 'URL RTSP con credenciales'),
            (r'logger\.\w+\(.*http[s]?://.*:.*@.*\)', 'URL HTTP con credenciales'),
            (r'logger\.\w+\(.*api[_-]?key.*\)', 'API key en log'),
            (r'logger\.\w+\(.*token.*\)', 'Token en log'),
            (r'logger\.\w+\(f["\'].*{.*password.*}.*["\']', 'Password en f-string'),
        ]
        
        for pattern, description in sensitive_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                analysis['sensitive_logs'].append(description)
                analysis['requires_sanitization'] = True
                
        return analysis
        
    def generate_updated_content(self, file_path: Path, analysis: Dict) -> str:
        """
        Genera el contenido actualizado del archivo.
        
        Args:
            file_path: Ruta del archivo
            analysis: Análisis del archivo
            
        Returns:
            Contenido actualizado
        """
        content = file_path.read_text(encoding='utf-8')
        
        # Determinar el nombre del módulo para el logger
        relative_path = file_path.relative_to(self.src_path)
        module_parts = list(relative_path.parts[:-1]) + [relative_path.stem]
        module_name = '.'.join(module_parts)
        
        # Reemplazar imports
        # Primero, eliminar imports de logging estándar
        content = re.sub(r'^import logging\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^from logging import .+$', '', content, flags=re.MULTILINE)
        content = re.sub(r'^import logging\..+$', '', content, flags=re.MULTILINE)
        
        # Agregar import de logging seguro después de otros imports
        # Buscar el último import
        import_match = None
        for match in re.finditer(r'^(?:import|from)\s+\S+.*$', content, re.MULTILINE):
            import_match = match
            
        if import_match:
            insert_pos = import_match.end()
            # Agregar el nuevo import
            new_import = "\nfrom services.logging_service import get_secure_logger"
            
            # Si necesita sanitización, agregar también sanitizers
            if analysis['requires_sanitization']:
                new_import += "\nfrom utils.sanitizers import sanitize_url, sanitize_command"
                
            content = content[:insert_pos] + new_import + content[insert_pos:]
        else:
            # Si no hay imports, agregar al principio después del docstring
            lines = content.split('\n')
            insert_line = 0
            in_docstring = False
            
            for i, line in enumerate(lines):
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    if not in_docstring:
                        in_docstring = True
                    else:
                        insert_line = i + 1
                        break
                        
            import_text = "from services.logging_service import get_secure_logger"
            if analysis['requires_sanitization']:
                import_text += "\nfrom utils.sanitizers import sanitize_url, sanitize_command"
                
            lines.insert(insert_line, import_text)
            content = '\n'.join(lines)
            
        # Reemplazar creación de logger
        # Buscar patrón específico según el tipo de archivo
        if 'BaseService' in content:
            # Es un servicio que hereda de BaseService
            content = re.sub(
                r'self\.logger\s*=\s*logging\.getLogger\([^)]*\)',
                f'self.logger = get_secure_logger("{module_name}")',
                content
            )
        else:
            # Otros casos
            content = re.sub(
                r'logger\s*=\s*logging\.getLogger\([^)]*\)',
                f'logger = get_secure_logger("{module_name}")',
                content
            )
            
        # Si hay logs sensibles, agregar comentarios de advertencia
        if analysis['requires_sanitization']:
            # Buscar logs con URLs
            content = re.sub(
                r'(logger\.\w+\()(.*)(rtsp://[^"\'\s]+)',
                lambda m: f'{m.group(1)}{m.group(2)}sanitize_url({m.group(3)})',
                content,
                flags=re.IGNORECASE
            )
            
            # TODO: Aquí se podrían agregar más transformaciones automáticas
            # Por ahora, agregar comentario de advertencia
            warning = """
# TODO: Este servicio contiene logs que pueden exponer información sensible.
# Revisar y aplicar sanitización donde sea necesario:
# - Usar sanitize_url() para URLs con credenciales
# - Usar sanitize_command() para comandos del sistema
# - No loggear passwords o tokens directamente
"""
            # Insertar después de los imports
            import_end = content.find('\n\n', content.find('from services.logging_service'))
            if import_end > 0:
                content = content[:import_end] + warning + content[import_end:]
                
        return content
        
    def update_file(self, file_path: Path, new_content: str) -> bool:
        """
        Actualiza un archivo con el nuevo contenido.
        
        Args:
            file_path: Ruta del archivo
            new_content: Nuevo contenido
            
        Returns:
            True si se actualizó exitosamente
        """
        if self.dry_run:
            print(f"[DRY RUN] Actualizaría: {file_path}")
            return True
            
        try:
            # Hacer backup
            backup_path = file_path.with_suffix('.py.bak')
            shutil.copy2(file_path, backup_path)
            
            # Escribir nuevo contenido
            file_path.write_text(new_content, encoding='utf-8')
            
            print(f"[OK] Actualizado: {file_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error actualizando {file_path}: {e}")
            return False
            
    def update_base_service(self) -> bool:
        """
        Actualiza BaseService para usar logging seguro por defecto.
        
        Returns:
            True si se actualizó exitosamente
        """
        base_service_path = self.services_path / "base_service.py"
        if not base_service_path.exists():
            return False
            
        content = base_service_path.read_text(encoding='utf-8')
        
        # Verificar si ya está actualizado
        if 'get_secure_logger' in content:
            print("BaseService ya usa logging seguro")
            return True
            
        # Actualizar imports
        content = re.sub(
            r'import logging',
            'from services.logging_service import get_secure_logger',
            content
        )
        
        # Actualizar creación de logger
        content = re.sub(
            r'self\.logger = logging\.getLogger\(self\.__class__\.__name__\)',
            'self.logger = get_secure_logger(f"{self.__module__}.{self.__class__.__name__}")',
            content
        )
        
        # También en el método alternativo si existe
        content = re.sub(
            r'self\.logger = logging\.getLogger\(f".*"\)',
            'self.logger = get_secure_logger(f"{self.__module__}.{self.__class__.__name__}")',
            content
        )
        
        return self.update_file(base_service_path, content)
        
    def generate_report(self) -> str:
        """
        Genera un reporte de los cambios realizados.
        
        Returns:
            Reporte en formato markdown
        """
        report = f"""# Reporte de Integración de Logging Seguro

**Fecha**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Modo**: {'DRY RUN' if self.dry_run else 'APLICADO'}

## Resumen

- Archivos analizados: {len(self.changes)}
- Archivos que requieren sanitización manual: {sum(1 for c in self.changes if c['analysis']['requires_sanitization'])}

## Cambios por Archivo

"""
        
        for change in self.changes:
            analysis = change['analysis']
            file_path = analysis['file']
            
            report += f"### {file_path.relative_to(self.src_path)}\n\n"
            
            if analysis['imports_to_update']:
                report += "**Imports actualizados**:\n"
                for imp in analysis['imports_to_update']:
                    report += f"- `{imp}`\n"
                report += "\n"
                
            if analysis['logger_creations']:
                report += "**Loggers actualizados**:\n"
                for logger in analysis['logger_creations']:
                    report += f"- `{logger or 'default'}`\n"
                report += "\n"
                
            if analysis['sensitive_logs']:
                report += "**⚠️ Logs sensibles detectados**:\n"
                for log in analysis['sensitive_logs']:
                    report += f"- {log}\n"
                report += "\n"
                
            report += "---\n\n"
            
        return report
        
    def run(self) -> Tuple[int, int]:
        """
        Ejecuta la actualización completa.
        
        Returns:
            Tupla de (archivos_actualizados, archivos_con_errores)
        """
        print(f"{'=' * 60}")
        print(f"Integración de Logging Seguro - {'DRY RUN' if self.dry_run else 'EJECUTANDO'}")
        print(f"{'=' * 60}\n")
        
        # Primero actualizar BaseService
        print("Actualizando BaseService...")
        self.update_base_service()
        print()
        
        # Encontrar servicios a actualizar
        print("Buscando servicios que usan logging estándar...")
        services = self.find_services_to_update()
        print(f"Encontrados: {len(services)} servicios\n")
        
        updated = 0
        errors = 0
        
        for service_path in services:
            print(f"Analizando: {service_path.relative_to(self.src_path)}")
            
            # Analizar archivo
            analysis = self.analyze_file(service_path)
            
            # Generar contenido actualizado
            new_content = self.generate_updated_content(service_path, analysis)
            
            # Actualizar archivo
            if self.update_file(service_path, new_content):
                updated += 1
            else:
                errors += 1
                
            # Guardar para reporte
            self.changes.append({
                'analysis': analysis,
                'new_content': new_content
            })
            
            print()
            
        # Generar reporte
        report = self.generate_report()
        report_path = Path(__file__).parent / f"logging_integration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.write_text(report, encoding='utf-8')
        
        print(f"\n{'=' * 60}")
        print(f"Resumen:")
        print(f"- Archivos actualizados: {updated}")
        print(f"- Errores: {errors}")
        print(f"- Reporte guardado en: {report_path}")
        print(f"{'=' * 60}")
        
        return updated, errors


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Actualiza servicios para usar el sistema de logging seguro'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Aplicar cambios (por defecto es dry-run)'
    )
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Solo generar reporte sin hacer cambios'
    )
    
    args = parser.parse_args()
    
    # Crear actualizador
    updater = LoggingIntegrationUpdater(dry_run=not args.apply)
    
    if args.report_only:
        # Solo analizar y generar reporte
        services = updater.find_services_to_update()
        for service in services:
            analysis = updater.analyze_file(service)
            updater.changes.append({'analysis': analysis})
            
        report = updater.generate_report()
        print(report)
    else:
        # Ejecutar actualización
        updated, errors = updater.run()
        
        if not args.apply:
            print("\n[AVISO] Esto fue un DRY RUN. Use --apply para aplicar los cambios.")
            
    return 0


if __name__ == "__main__":
    sys.exit(main())