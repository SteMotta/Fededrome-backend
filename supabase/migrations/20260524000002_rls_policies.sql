-- ─── Abilita RLS su tutte le tabelle ───────────────────────────────────────
ALTER TABLE public.profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.followers   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movie_logs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist   ENABLE ROW LEVEL SECURITY;

-- ─── Disabilita pg_graphql per proteggere la struttura del database ──────────
COMMENT ON TABLE public.profiles IS '@graphql(disable: true)';
COMMENT ON TABLE public.followers IS '@graphql(disable: true)';
COMMENT ON TABLE public.movie_logs IS '@graphql(disable: true)';
COMMENT ON TABLE public.watchlist IS '@graphql(disable: true)';

-- ─── Profiles ──────────────────────────────────────────────────────────────
CREATE POLICY "profiles_select_public"
  ON public.profiles FOR SELECT USING (true);

CREATE POLICY "profiles_update_own"
  ON public.profiles FOR UPDATE USING ((select auth.uid()) = id);

-- ─── Movie Logs ────────────────────────────────────────────────────────────
-- I log sono pubblici (come su Letterboxd)
CREATE POLICY "logs_select_public"
  ON public.movie_logs FOR SELECT USING (true);

CREATE POLICY "logs_insert_own"
  ON public.movie_logs FOR INSERT WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "logs_update_own"
  ON public.movie_logs FOR UPDATE USING ((select auth.uid()) = user_id);

CREATE POLICY "logs_delete_own"
  ON public.movie_logs FOR DELETE USING ((select auth.uid()) = user_id);

-- ─── Watchlist ─────────────────────────────────────────────────────────────
-- La watchlist è privata
CREATE POLICY "watchlist_select_own"
  ON public.watchlist FOR SELECT USING ((select auth.uid()) = user_id);

CREATE POLICY "watchlist_insert_own"
  ON public.watchlist FOR INSERT WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "watchlist_delete_own"
  ON public.watchlist FOR DELETE USING ((select auth.uid()) = user_id);

-- ─── Followers ─────────────────────────────────────────────────────────────
CREATE POLICY "followers_select_public"
  ON public.followers FOR SELECT USING (true);

CREATE POLICY "followers_insert_own"
  ON public.followers FOR INSERT WITH CHECK ((select auth.uid()) = follower_id);

CREATE POLICY "followers_delete_own"
  ON public.followers FOR DELETE USING ((select auth.uid()) = follower_id);

-- ─── Storage: bucket avatar ────────────────────────────────────────────────
-- Nota: Essendo un bucket pubblico (public = true), gli oggetti sono accessibili
-- pubblicamente tramite URL diretto. Non è necessaria una policy SELECT di tipo broad,
-- il che previene l'enumerazione (listing) indesiderata dei file da parte dei client.
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT DO NOTHING;

CREATE POLICY "avatars_upload_own"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars'
    AND (select auth.uid())::text = (storage.foldername(name))[1]
  );

CREATE POLICY "avatars_update_own"
  ON storage.objects FOR UPDATE
  USING (
    bucket_id = 'avatars'
    AND (select auth.uid())::text = (storage.foldername(name))[1]
  );

CREATE POLICY "avatars_select_own"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'avatars'
    AND (select auth.uid())::text = (storage.foldername(name))[1]
  );