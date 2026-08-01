-- Run this if you already created the facilities table before this column existed
alter table facilities add column if not exists geocode_precision text;
