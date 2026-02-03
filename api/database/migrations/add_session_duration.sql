-- Migration: Add duration_seconds to sessions table
-- This allows us to track actual session time instead of estimating from interactions

ALTER TABLE public.sessions 
ADD COLUMN IF NOT EXISTS duration_seconds INTEGER;

-- For existing sessions, calculate duration from created_at and ended_at if both exist
UPDATE public.sessions
SET duration_seconds = EXTRACT(EPOCH FROM (ended_at - created_at))::INTEGER
WHERE ended_at IS NOT NULL AND created_at IS NOT NULL AND duration_seconds IS NULL;

