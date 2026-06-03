-- Migration: Revoke SELECT on all tables from anon and authenticated to resolve pg_graphql exposure warnings

REVOKE SELECT ON public.profiles FROM anon, authenticated;
REVOKE SELECT ON public.followers FROM anon, authenticated;
REVOKE SELECT ON public.movie_logs FROM anon, authenticated;
REVOKE SELECT ON public.watchlist FROM anon, authenticated;
REVOKE SELECT ON public.custom_lists FROM anon, authenticated;
REVOKE SELECT ON public.custom_list_movies FROM anon, authenticated;
