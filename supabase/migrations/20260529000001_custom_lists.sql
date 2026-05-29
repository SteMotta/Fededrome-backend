-- Migration: Create Custom Lists tables

CREATE TABLE public.custom_lists (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

REVOKE SELECT ON public.custom_lists FROM anon, authenticated;
CREATE INDEX idx_custom_lists_user ON public.custom_lists(user_id);

CREATE TRIGGER custom_lists_updated_at
  BEFORE UPDATE ON public.custom_lists
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE public.custom_list_movies (
    list_id    BIGINT NOT NULL REFERENCES public.custom_lists(id) ON DELETE CASCADE,
    tmdb_id    INTEGER NOT NULL,
    added_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (list_id, tmdb_id)
);

REVOKE SELECT ON public.custom_list_movies FROM anon, authenticated;
CREATE INDEX idx_custom_list_movies_list ON public.custom_list_movies(list_id);
