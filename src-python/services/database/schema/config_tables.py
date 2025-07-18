"""
Tablas de configuración.

Contiene las definiciones para gestión de configuración:
- system_config: Configuración global del sistema
- config_templates: Plantillas de configuración por marca/modelo
"""

# Tabla de configuración global
SYSTEM_CONFIG_TABLE = """
    CREATE TABLE system_config (
        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        setting_key TEXT NOT NULL,
        setting_value TEXT NOT NULL,
        setting_type TEXT DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'float', 'boolean', 'json')),
        is_encrypted BOOLEAN DEFAULT 0,
        is_user_configurable BOOLEAN DEFAULT 1,
        default_value TEXT,
        description TEXT,
        validation_rules JSON,          -- Reglas de validación
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by TEXT,
        UNIQUE(category, setting_key)
    )
"""

# Tabla de plantillas de configuración
# APIs FALTANTES:
# - GET /templates - Listar plantillas
# - POST /templates - Crear plantilla
# - GET /templates/{id} - Obtener plantilla
# - PUT /templates/{id} - Actualizar plantilla
# - DELETE /templates/{id} - Eliminar plantilla
# - POST /templates/{id}/apply - Aplicar plantilla a cámara
CONFIG_TEMPLATES_TABLE = """
    CREATE TABLE config_templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT NOT NULL UNIQUE,
        template_type TEXT NOT NULL,    -- camera_brand, protocol, etc.
        brand TEXT,
        model_pattern TEXT,             -- Patrón regex para matching de modelos
        configuration JSON NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT
    )
"""


def get_config_tables():
    """Retorna lista de tuplas (nombre_tabla, sql_create)."""
    return [
        ('system_config', SYSTEM_CONFIG_TABLE),
        ('config_templates', CONFIG_TEMPLATES_TABLE)
    ]


def get_table_names():
    """Retorna solo los nombres de las tablas de configuración."""
    return [name for name, _ in get_config_tables()]