-- Run this in Supabase SQL Editor before using the sync service.
-- Tracks whether a facility is still listed in the government's latest
-- data (rather than hard-deleting rows that disappear from a refresh --
-- preserves history and anything tied to the facility, like vacancy data).
alter table facilities add column if not exists source_still_listed boolean default true;
alter table facilities add column if not exists last_synced_at timestamptz;
