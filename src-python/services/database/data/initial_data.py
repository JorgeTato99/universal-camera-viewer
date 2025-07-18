"""
Datos iniciales para la base de datos.

Este módulo contiene todos los datos que se insertan
al crear una nueva base de datos, incluyendo configuraciones
por defecto y plantillas.
"""

import json


def get_system_config_data():
    """Retorna las configuraciones por defecto del sistema."""
    return [
        # (category, setting_key, setting_value, setting_type, is_user_configurable, description)
        ('general', 'app_name', 'Universal Camera Viewer', 'string', 0, 'Nombre de la aplicación'),
        ('general', 'version', '0.9.1', 'string', 0, 'Versión de la aplicación'),
        ('general', 'theme', 'light', 'string', 1, 'Tema de la interfaz'),
        ('network', 'default_timeout', '10', 'integer', 1, 'Timeout por defecto en segundos'),
        ('network', 'max_retries', '3', 'integer', 1, 'Máximo de reintentos de conexión'),
        ('streaming', 'default_fps', '15', 'integer', 1, 'FPS por defecto para streaming'),
        ('streaming', 'buffer_size', '1048576', 'integer', 1, 'Tamaño del buffer en bytes'),
        ('storage', 'snapshot_retention_days', '30', 'integer', 1, 'Días de retención de snapshots'),
        ('storage', 'max_snapshot_size_mb', '10', 'integer', 1, 'Tamaño máximo de snapshot en MB'),
        ('security', 'encryption_algorithm', 'AES256', 'string', 0, 'Algoritmo de encriptación'),
        ('security', 'session_timeout_minutes', '30', 'integer', 1, 'Timeout de sesión en minutos'),
        ('mediamtx', 'default_rtsp_port', '8554', 'integer', 1, 'Puerto RTSP por defecto para MediaMTX'),
        ('mediamtx', 'default_api_port', '9997', 'integer', 1, 'Puerto API por defecto para MediaMTX'),
        ('mediamtx', 'health_check_interval', '30', 'integer', 1, 'Intervalo de health check en segundos'),
        ('mediamtx', 'max_reconnect_attempts', '3', 'integer', 1, 'Máximo de intentos de reconexión'),
        ('mediamtx', 'reconnect_delay', '5', 'float', 1, 'Delay entre reconexiones en segundos')
    ]


def get_config_templates_data():
    """Retorna las plantillas de configuración por marca."""
    templates = []
    
    # Plantilla Dahua
    dahua_config = {
        'protocols': [
            {'type': 'ONVIF', 'port': 80},
            {'type': 'RTSP', 'port': 554}
        ],
        'endpoints': {
            'rtsp_main': 'rtsp://{ip}:{port}/cam/realmonitor?channel=1&subtype=0',
            'rtsp_sub': 'rtsp://{ip}:{port}/cam/realmonitor?channel=1&subtype=1',
            'snapshot': 'http://{ip}/cgi-bin/snapshot.cgi'
        }
    }
    templates.append((
        'Dahua Default',           # template_name
        'camera_brand',            # template_type
        'dahua',                   # brand
        None,                      # model_pattern
        json.dumps(dahua_config)   # configuration
    ))
    
    # Plantilla Hikvision
    hikvision_config = {
        'protocols': [
            {'type': 'ONVIF', 'port': 80},
            {'type': 'RTSP', 'port': 554}
        ],
        'endpoints': {
            'rtsp_main': 'rtsp://{ip}:{port}/Streaming/Channels/101',
            'rtsp_sub': 'rtsp://{ip}:{port}/Streaming/Channels/102',
            'snapshot': 'http://{ip}/ISAPI/Streaming/channels/101/picture'
        }
    }
    templates.append((
        'Hikvision Default',
        'camera_brand',
        'hikvision',
        None,
        json.dumps(hikvision_config)
    ))
    
    # Plantilla TP-Link
    tplink_config = {
        'protocols': [
            {'type': 'ONVIF', 'port': 2020},
            {'type': 'RTSP', 'port': 554}
        ],
        'endpoints': {
            'rtsp_main': 'rtsp://{ip}:{port}/stream1',
            'rtsp_sub': 'rtsp://{ip}:{port}/stream2',
            'snapshot': 'http://{ip}/cgi-bin/snapshot.cgi'
        }
    }
    templates.append((
        'TP-Link Default',
        'camera_brand',
        'tplink',
        None,
        json.dumps(tplink_config)
    ))
    
    return templates


def insert_initial_data(cursor):
    """
    Inserta todos los datos iniciales en la base de datos.
    
    Args:
        cursor: Cursor de SQLite para ejecutar las inserciones
    """
    # Insertar configuraciones del sistema
    config_data = get_system_config_data()
    cursor.executemany("""
        INSERT INTO system_config (category, setting_key, setting_value, setting_type, is_user_configurable, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, config_data)
    
    # Insertar plantillas de configuración
    template_data = get_config_templates_data()
    cursor.executemany("""
        INSERT INTO config_templates (template_name, template_type, brand, model_pattern, configuration)
        VALUES (?, ?, ?, ?, ?)
    """, template_data)


def get_initial_data_summary():
    """Retorna un resumen de los datos iniciales que se insertarán."""
    return {
        'system_config': len(get_system_config_data()),
        'config_templates': len(get_config_templates_data())
    }