-- Tablas de NexusSec AI. Ejecútalo en el editor SQL de Supabase.
-- La búsqueda actual es por texto. La columna embedding es opcional.

create table if not exists public.knowledge (
    id bigint generated always as identity primary key,
    content text not null,
    source text,
    tags text,
    filename text,
    page_number integer,
    embedding jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.chat_history (
    id bigint generated always as identity primary key,
    session_id text not null,
    title text,
    role text not null,
    content text not null,
    created_at timestamptz not null default now()
);

create index if not exists knowledge_content_idx on public.knowledge using gin (to_tsvector('spanish', content));
create index if not exists chat_history_session_idx on public.chat_history (session_id, created_at);
