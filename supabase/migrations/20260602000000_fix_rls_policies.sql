-- Migration: Fix RLS policies and restore standard SELECT privileges

-- 1. Enable RLS on custom_lists and custom_list_movies
ALTER TABLE public.custom_lists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.custom_list_movies ENABLE ROW LEVEL SECURITY;

-- 2. Disable pg_graphql for custom_lists and custom_list_movies to protect the schema structure
COMMENT ON TABLE public.custom_lists IS '@graphql(disable: true)';
COMMENT ON TABLE public.custom_list_movies IS '@graphql(disable: true)';

-- 3. Grant SELECT back to anon and authenticated roles to support standard Supabase client operations
GRANT SELECT ON public.profiles TO anon, authenticated;
GRANT SELECT ON public.followers TO anon, authenticated;
GRANT SELECT ON public.movie_logs TO anon, authenticated;
GRANT SELECT ON public.watchlist TO anon, authenticated;
GRANT SELECT ON public.custom_lists TO anon, authenticated;
GRANT SELECT ON public.custom_list_movies TO anon, authenticated;

-- 4. Create RLS policies for custom_lists
CREATE POLICY "lists_select_authorized" ON public.custom_lists
  FOR SELECT USING (is_public = true OR (select auth.uid()) = user_id);

CREATE POLICY "lists_insert_own" ON public.custom_lists
  FOR INSERT WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "lists_update_own" ON public.custom_lists
  FOR UPDATE USING ((select auth.uid()) = user_id);

CREATE POLICY "lists_delete_own" ON public.custom_lists
  FOR DELETE USING ((select auth.uid()) = user_id);

-- 5. Create RLS policies for custom_list_movies
CREATE POLICY "list_movies_select_authorized" ON public.custom_list_movies
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.custom_lists
      WHERE id = list_id AND (is_public = true OR user_id = (select auth.uid()))
    )
  );

CREATE POLICY "list_movies_insert_own" ON public.custom_list_movies
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.custom_lists
      WHERE id = list_id AND user_id = (select auth.uid())
    )
  );

CREATE POLICY "list_movies_delete_own" ON public.custom_list_movies
  FOR DELETE USING (
    EXISTS (
      SELECT 1 FROM public.custom_lists
      WHERE id = list_id AND user_id = (select auth.uid())
    )
  );
