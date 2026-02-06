-- Add a per-child curriculum coverage snapshot (token-efficient for advisor agent)
-- Stores aggregated coverage across sessions (not per-session).

ALTER TABLE public.children
ADD COLUMN IF NOT EXISTS curriculum_coverage JSONB;


