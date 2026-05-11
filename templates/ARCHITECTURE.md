# Architecture

Updated: <!-- YYYY-MM-DD -->

## Overview

<!-- High-level description or ASCII diagram of the system.
     An agent reads this to understand where new code goes without breaking structure.
     Example:

     Browser → Nginx → FastAPI app → PostgreSQL
                                  → Redis (queue)
                                  → OpenAI API
-->

## Components

<!-- One subsection per major component. Copy the block as needed. -->

### Component: <!-- name -->

- Purpose:       <!-- what it does -->
- Language/tool: <!-- Python 3.12, TypeScript 5, Rust, etc. -->
- Entry point:   <!-- file path -->
- Inputs:        <!-- what it receives -->
- Outputs:       <!-- what it produces -->
- Dependencies:  <!-- other components or external services it calls -->

<!--
### Component: (add more as needed)
-->

## Data flow

<!-- How data moves through the system end to end, for the most important workflow.
     A numbered sequence is fine.
     Example:
     1. User submits ticker via POST /research
     2. API validates and enqueues job to Redis
     3. Orchestrator dequeues and spawns 4 synthesis agents in parallel
     4. Each agent calls OpenAI, writes results to Postgres
     5. Evaluation harness scores results, stores grade
     6. Report generator assembles final PDF
     7. Webhook notifies caller -->

## Storage

Database(s):      <!-- e.g. PostgreSQL 16 on VPS, schema at src/db/schema.sql -->
Schema location:  <!-- path to migration files or schema file -->
Object storage:   <!-- e.g. S3-compatible via MinIO, none -->
Cache:            <!-- e.g. Redis 7, none -->
Backup strategy:  <!-- e.g. pg_dump daily to S3, none yet -->

## External services

<!-- APIs and services the project depends on. -->

| Service | Purpose | Auth method | Rate limit / quota |
|---------|---------|-------------|-------------------|
| —       | —       | —           | —                 |

## Deployment topology

<!-- Where each component runs.
     Example:
     - FastAPI app:  systemd service on Ubuntu 22.04 VPS (147.xxx.xxx.xxx)
     - Frontend:     Vercel (auto-deploy OFF — see AGENTS.md)
     - Database:     Postgres on same VPS, port 5432, local-only
     - Redis:        Same VPS, port 6379, local-only -->

## Key tradeoffs and constraints

<!-- Decisions baked into the architecture and what they cost.
     These are NOT individual ADRs (those go in DECISIONS.md) — this is the
     structural constraints every new feature must work within.
     Example:
     - Single-server for now: simpler ops, but no horizontal scaling
     - Sync OpenAI calls: simpler code, but each request ties up a thread
     - pgvector for embeddings: avoids a second DB, but limits vector index size -->
