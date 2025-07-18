"""
Definiciones de triggers para integridad y automatización.

Este módulo contiene todos los triggers de la base de datos
para mantener integridad referencial y automatizar actualizaciones.
"""


def get_updated_at_triggers():
    """Triggers para actualizar automáticamente el campo updated_at."""
    tables_with_updated_at = [
        'cameras', 'camera_credentials', 'camera_protocols', 
        'camera_endpoints', 'stream_profiles', 'camera_statistics',
        'system_config', 'config_templates', 'mediamtx_servers',
        'camera_publications', 'mediamtx_paths'
    ]
    
    triggers = []
    for table in tables_with_updated_at:
        trigger_sql = f"""
            CREATE TRIGGER update_{table}_timestamp 
            AFTER UPDATE ON {table}
            BEGIN
                UPDATE {table} 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE rowid = NEW.rowid;
            END
        """
        triggers.append(trigger_sql)
    
    return triggers


def get_integrity_triggers():
    """Triggers para mantener integridad de datos."""
    return [
        # Trigger para validar que solo hay un protocolo primario por cámara
        """
        CREATE TRIGGER enforce_single_primary_protocol
        BEFORE INSERT ON camera_protocols
        WHEN NEW.is_primary = 1
        BEGIN
            UPDATE camera_protocols 
            SET is_primary = 0 
            WHERE camera_id = NEW.camera_id AND is_primary = 1;
        END
        """,
        
        # Trigger para crear estadísticas cuando se crea una cámara
        """
        CREATE TRIGGER create_camera_statistics
        AFTER INSERT ON cameras
        BEGIN
            INSERT INTO camera_statistics (camera_id)
            VALUES (NEW.camera_id);
        END
        """,
        
        # Trigger para validar que solo hay una credencial por defecto por cámara
        """
        CREATE TRIGGER enforce_single_default_credential
        BEFORE INSERT ON camera_credentials
        WHEN NEW.is_default = 1
        BEGIN
            UPDATE camera_credentials 
            SET is_default = 0 
            WHERE camera_id = NEW.camera_id AND is_default = 1;
        END
        """,
        
        # Trigger para validar que solo hay un servidor MediaMTX por defecto
        """
        CREATE TRIGGER enforce_single_default_mediamtx_server
        BEFORE INSERT ON mediamtx_servers
        WHEN NEW.is_default = 1
        BEGIN
            UPDATE mediamtx_servers 
            SET is_default = 0 
            WHERE is_default = 1;
        END
        """,
    ]


def get_update_triggers():
    """Triggers para actualizaciones específicas en UPDATE."""
    return [
        # Trigger para actualizar protocolo primario en UPDATE
        """
        CREATE TRIGGER enforce_single_primary_protocol_update
        BEFORE UPDATE ON camera_protocols
        WHEN NEW.is_primary = 1 AND OLD.is_primary = 0
        BEGIN
            UPDATE camera_protocols 
            SET is_primary = 0 
            WHERE camera_id = NEW.camera_id AND is_primary = 1 AND protocol_id != NEW.protocol_id;
        END
        """,
        
        # Trigger para actualizar credencial por defecto en UPDATE
        """
        CREATE TRIGGER enforce_single_default_credential_update
        BEFORE UPDATE ON camera_credentials
        WHEN NEW.is_default = 1 AND OLD.is_default = 0
        BEGIN
            UPDATE camera_credentials 
            SET is_default = 0 
            WHERE camera_id = NEW.camera_id AND is_default = 1 AND credential_id != NEW.credential_id;
        END
        """,
        
        # Trigger para actualizar servidor MediaMTX por defecto en UPDATE
        """
        CREATE TRIGGER enforce_single_default_mediamtx_server_update
        BEFORE UPDATE ON mediamtx_servers
        WHEN NEW.is_default = 1 AND OLD.is_default = 0
        BEGIN
            UPDATE mediamtx_servers 
            SET is_default = 0 
            WHERE is_default = 1 AND server_id != NEW.server_id;
        END
        """,
    ]


def get_all_triggers():
    """Retorna todos los triggers de la base de datos."""
    triggers = []
    triggers.extend(get_updated_at_triggers())
    triggers.extend(get_integrity_triggers())
    triggers.extend(get_update_triggers())
    return triggers


def get_trigger_count():
    """Retorna el número total de triggers."""
    return len(get_all_triggers())


def get_triggers_by_table(table_name):
    """Retorna los triggers asociados a una tabla específica."""
    all_triggers = get_all_triggers()
    table_triggers = []
    
    for trigger in all_triggers:
        if f" ON {table_name}" in trigger or f"_{table_name}_" in trigger:
            table_triggers.append(trigger)
    
    return table_triggers