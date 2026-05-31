-- Migration: Add is_public column to custom_lists
ALTER TABLE public.custom_lists ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;
