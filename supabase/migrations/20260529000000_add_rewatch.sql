-- Migration: Add is_rewatch to movie_logs

ALTER TABLE public.movie_logs 
ADD COLUMN is_rewatch BOOLEAN DEFAULT FALSE;

-- We don't need to update RLS policies since the new column is part of an existing table 
-- that already has policies for INSERT/UPDATE/SELECT for the owning user.
