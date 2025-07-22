-- Índices optimizados para historial de publicaciones MediaMTX
-- Estos índices mejoran el rendimiento de las consultas más frecuentes

-- Índice compuesto para filtros comunes de historial
CREATE INDEX IF NOT EXISTS idx_publication_history_filters 
ON publication_history(camera_id, start_time DESC, termination_reason);

-- Índice para búsquedas por rango de tiempo
CREATE INDEX IF NOT EXISTS idx_publication_history_time_range
ON publication_history(start_time DESC, end_time);

-- Índice para filtros de duración
CREATE INDEX IF NOT EXISTS idx_publication_history_duration
ON publication_history(duration_seconds, start_time DESC);

-- Índice para búsquedas por error
CREATE INDEX IF NOT EXISTS idx_publication_history_errors
ON publication_history(error_count, termination_reason)
WHERE error_count > 0;

-- Índice para estadísticas por servidor
CREATE INDEX IF NOT EXISTS idx_publication_history_server_stats
ON publication_history(server_id, start_time DESC);

-- Índice para limpieza eficiente
CREATE INDEX IF NOT EXISTS idx_publication_history_cleanup
ON publication_history(start_time, error_count, duration_seconds);

-- Trigger para calcular duración automáticamente
CREATE TRIGGER IF NOT EXISTS calculate_duration_on_insert
AFTER INSERT ON publication_history
FOR EACH ROW
WHEN NEW.end_time IS NOT NULL AND NEW.duration_seconds IS NULL
BEGIN
    UPDATE publication_history 
    SET duration_seconds = CAST((julianday(NEW.end_time) - julianday(NEW.start_time)) * 86400 AS INTEGER)
    WHERE history_id = NEW.history_id;
END;

-- Vista para estadísticas frecuentes
CREATE VIEW IF NOT EXISTS v_publication_stats AS
SELECT 
    camera_id,
    COUNT(*) as total_sessions,
    AVG(duration_seconds) as avg_duration,
    SUM(total_frames) as total_frames,
    SUM(total_data_mb) as total_data_mb,
    MAX(max_viewers) as peak_viewers,
    SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) as error_sessions,
    DATE(start_time) as session_date
FROM publication_history
GROUP BY camera_id, DATE(start_time);

-- Índice en la vista para consultas rápidas
CREATE INDEX IF NOT EXISTS idx_v_publication_stats_date
ON v_publication_stats(session_date DESC, camera_id);