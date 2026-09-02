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
    seq              bigserial not null,          -- порядок вставки, по нему пересчитываем цепочку
    request_id       text,
    requested_at     timestamptz not null default now(),
    normalized_query text,
    list_version     text,
    outcome          text,
    top_score        numeric,
    reason_codes     text[],
    candidates       jsonb,
    reviewer         text,                        -- заполняется при ручном ревью
    reviewed_at      timestamptz,
    review_outcome   text,
    review_notes     text,
    previous_hash    text,
    event_hash       text
);

create table if not exists review_events (
    review_id     uuid primary key,
    seq           bigserial not null,
    decision_id   uuid not null references screening_decisions(decision_id),
    reviewer      text not null,
    reviewed_at   timestamptz not null default now(),
    outcome       text not null,
    notes         text,
    previous_hash text,
    event_hash    text
);

-- голова каждой цепочки: последний хеш. читается под FOR UPDATE, чтобы запись была последовательной
create table if not exists audit_chain_head (
    chain_name text primary key,
    event_hash text
);
insert into audit_chain_head (chain_name, event_hash) values ('decisions', null), ('reviews', null)
on conflict do nothing;

create table if not exists review_queue (
    decision_id uuid primary key references screening_decisions(decision_id),
    priority    int not null default 5,
    status      text not null default 'open',
    created_at  timestamptz not null default now()
);
