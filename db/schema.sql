create extension if not exists pg_trgm;

create table if not exists sanction_entries (
    entity_id       text primary key,
    source_list     text not null,
    entity_type     text,
    primary_name    text not null,
    normalized_name text not null,
    programs        text[]  not null default '{}',
    countries       text[]  not null default '{}',
    dates_of_birth  text[]  not null default '{}',
    identifiers     jsonb   not null default '[]',
    aliases         jsonb   not null default '[]',
    source_version  text not null,
    loaded_at       timestamptz not null default now()
);

create index if not exists sanction_entries_normalized_name_idx on sanction_entries using gin (normalized_name gin_trgm_ops);

create table if not exists screening_decisions (
    decision_id      uuid primary key,
    request_id       text,
    requested_at     timestamptz not null default now(),
    normalized_query text,
    list_version     text,
    outcome          text,
    top_score        numeric,
    reason_codes     text[],
    candidates       jsonb,
    previous_hash    text,
    event_hash       text
);
