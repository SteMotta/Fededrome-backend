-- ─── Profiles ──────────────────────────────────────────────────────────────
CREATE TABLE public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username    TEXT UNIQUE NOT NULL,
    email       TEXT NOT NULL,
    bio         TEXT DEFAULT '',
    avatar_url  TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.profiles FROM anon, authenticated;

-- Creazione schema privato per funzioni di trigger interne (non esposte alle API REST)
CREATE SCHEMA IF NOT EXISTS private;

-- Trigger: crea profilo automaticamente alla registrazione
CREATE OR REPLACE FUNCTION private.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, username)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1))
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION private.handle_new_user();

-- ─── Followers ─────────────────────────────────────────────────────────────
CREATE TABLE public.followers (
    follower_id  UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    following_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id)
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.followers FROM anon, authenticated;

-- ─── Movie Logs ────────────────────────────────────────────────────────────
CREATE TABLE public.movie_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tmdb_id         INTEGER NOT NULL,
    watched_date    DATE NOT NULL,
    rating          NUMERIC(2,1) CHECK (rating >= 0.5 AND rating <= 5.0),
    review          TEXT DEFAULT '',
    liked           BOOLEAN DEFAULT FALSE,
    genres_snapshot JSONB DEFAULT '[]',
    runtime_minutes SMALLINT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.movie_logs FROM anon, authenticated;

CREATE INDEX idx_logs_user_date ON public.movie_logs(user_id, watched_date DESC);
CREATE INDEX idx_logs_tmdb      ON public.movie_logs(tmdb_id);

-- Trigger: aggiorna updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql SET search_path = public;

CREATE TRIGGER movie_logs_updated_at
  BEFORE UPDATE ON public.movie_logs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── Watchlist ─────────────────────────────────────────────────────────────
CREATE TABLE public.watchlist (
    user_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tmdb_id    INTEGER NOT NULL,
    added_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, tmdb_id)
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.watchlist FROM anon, authenticated;

CREATE INDEX idx_watchlist_user ON public.watchlist(user_id);