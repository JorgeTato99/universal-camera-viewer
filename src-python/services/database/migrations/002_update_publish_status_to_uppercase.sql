-- Migration: Update PublishStatus values from lowercase to uppercase
-- Date: 2025-01-23
-- Purpose: Synchronize backend enum values with frontend expectations

-- IMPORTANT: This migration updates the publish status values to match
-- the frontend TypeScript enum which uses uppercase values.
-- This resolves the type inconsistency detected in Phase 4.1 testing.

BEGIN;

-- Step 1: Temporarily disable the CHECK constraint
-- Note: SQLite doesn't support ALTER TABLE DROP CONSTRAINT
-- so we need to recreate the table

-- Create temporary table with new constraint
CREATE TABLE publishing_states_temp (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    publication_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('IDLE', 'STARTING', 'PUBLISHING', 'STOPPED', 'ERROR')),
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    publish_path TEXT,
    ffmpeg_pid INTEGER,
    is_reconnecting BOOLEAN DEFAULT FALSE,
    metadata TEXT,
    FOREIGN KEY (publication_id) REFERENCES active_publications(publication_id) ON DELETE CASCADE
);

-- Step 2: Copy data with uppercase status values
INSERT INTO publishing_states_temp (
    state_id, publication_id, status, started_at, last_updated,
    error_message, error_count, publish_path, ffmpeg_pid,
    is_reconnecting, metadata
)
SELECT 
    state_id, 
    publication_id,
    UPPER(status) as status,  -- Convert to uppercase
    started_at,
    last_updated,
    error_message,
    error_count,
    publish_path,
    ffmpeg_pid,
    is_reconnecting,
    metadata
FROM publishing_states;

-- Step 3: Drop old table and rename new one
DROP TABLE publishing_states;
ALTER TABLE publishing_states_temp RENAME TO publishing_states;

-- Step 4: Recreate indexes
CREATE INDEX idx_publishing_states_status ON publishing_states(status);
CREATE INDEX idx_publishing_states_publication ON publishing_states(publication_id);

-- Step 5: Update any existing history records (if they store status)
-- Note: The publication_history table uses termination_reason, not status
-- but we should check for any status references

-- Add migration record
INSERT INTO schema_migrations (version, applied_at, description)
VALUES (
    '002',
    CURRENT_TIMESTAMP,
    'Update PublishStatus values from lowercase to uppercase for frontend compatibility'
);

COMMIT;

-- Verification query (run after migration)
-- SELECT DISTINCT status FROM publishing_states;
-- Expected: IDLE, STARTING, PUBLISHING, STOPPED, ERROR