-- Migration 001 — initial schema
-- Run this in the Supabase SQL editor to initialize all tables.

-- Enable UUID generation
create extension if not exists "pgcrypto";

-- ─── tasks ────────────────────────────────────────────────────────────────────
create table if not exists tasks (
    id           uuid        primary key default gen_random_uuid(),
    title        text        not null,
    description  text,
    due_date     date,
    priority     text        not null default 'medium'
                             check (priority in ('low', 'medium', 'high')),
    status       text        not null default 'pending'
                             check (status in ('pending', 'in_progress', 'done')),
    created_at   timestamptz not null default now(),
    reminded_at  timestamptz
);

-- ─── resumes ──────────────────────────────────────────────────────────────────
create table if not exists resumes (
    id          uuid        primary key default gen_random_uuid(),
    raw_text    text        not null,
    uploaded_at timestamptz not null default now()
);

-- ─── interview_sessions ───────────────────────────────────────────────────────
create table if not exists interview_sessions (
    id         uuid        primary key default gen_random_uuid(),
    company    text        not null,
    jd_text    text        not null,
    resume_id  uuid        references resumes(id) on delete set null,
    insights   text,
    questions  jsonb       not null default '[]'::jsonb,
    answers    jsonb       not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

-- ─── indexes ──────────────────────────────────────────────────────────────────
create index if not exists idx_tasks_status      on tasks (status);
create index if not exists idx_tasks_due_date    on tasks (due_date);
create index if not exists idx_sessions_resume   on interview_sessions (resume_id);
create index if not exists idx_sessions_company  on interview_sessions (company);
