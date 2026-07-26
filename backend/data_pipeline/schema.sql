-- schema.sql
-- Run this in Supabase SQL Editor to create the facilities table.
-- Source: 桃園市日間照顧、小規模多機能服務提供單位名冊 (opendata.tycg.gov.tw)

create table if not exists facilities (
  id bigint generated always as identity primary key,
  source_seq text,                 -- 序號 from source CSV, for traceability
  district text not null,          -- 行政區 e.g. 桃園區, 中壢區
  org_type text,                   -- 單位性質 e.g. 財團法人, 社團法人
  name text not null,              -- 服務單位
  address text not null,
  phone text,
  services text,                   -- 服務項目 (raw text from source)
  status text,                     -- 服務情形 (raw text from source)
  lat double precision,
  lng double precision,
  vacancy_status text default 'unknown',  -- 'available' | 'full' | 'unknown' — updated by admin panel later (Week 2)
  vacancy_updated_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_facilities_district on facilities (district);
create index if not exists idx_facilities_location on facilities (lat, lng);

-- Row Level Security: public read, writes locked down (admin panel will
-- use a service role key or authenticated policy in Week 2)
alter table facilities enable row level security;

create policy "Public can read facilities"
  on facilities for select
  using (true);
