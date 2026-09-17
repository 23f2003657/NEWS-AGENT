# AGENTS.md — AI News Agent (Team Chronologix)

Context file for AI coding agents. Keep this file updated as the project evolves,
especially the **Progress Tracker** and **Decisions & Open Questions** sections.

---

## 1. Project Summary

AI moves faster than any single reader can track. The **AI News Agent** ingests
AI-specific news, research papers, and tool releases, then turns them into short,
sourced summaries — organized into **Stories** (evolving storylines shown as
chronological timelines) rather than a flat feed.

> Design driver (instructor feedback): *"bridge the gap in the chronology of
> news — how news is progressing."* Given a stream of individually-published
> articles, reconstruct the evolving storylines they belong to and present each
> storyline as an ordered timeline.

## 2. Source Documents

| Doc | Location | Notes |
|---|---|---|
| Original proposal (v1.1) | `docs/AI_News_Agent_Proposal_v3 (1).pdf` | PDF only. Broader multi-source scope. |
| **Revised design (HLD + LLD)** | `docs/AI_News_Agent_HLD_LLD.md` | **Authoritative spec for the prototype.** Supersedes proposal where they conflict. |

## 3. Key Scope Changes (prototype vs. original proposal)

1. **Chronology is the core deliverable.** New first-class entity: **Story**.
   Every ingested item is classified as: duplicate / new chapter of an existing
   story / new story.
2. **Single news API** for ingestion (plus arXiv + GitHub). No multi-outlet
   cross-source dedup for news.
3. Story matching = semantic similarity + temporal gap (see §5 thresholds).
4. New API endpoints: `/stories`, `/stories/{id}/timeline`.
5. New frontend **Timeline view** (chapter-by-chapter vertical layout).

## 4. Tech Stack

| Component | Choice |
|---|---|
| Backend | Python, FastAPI |
| Agent orchestration | LangGraph (ambiguous-band story-matching decision, later phase) |
| Relational store | Postgres (`items`, `stories`) |
| Vector store | Chroma (`item_vectors`, `story_centroids`) |
| Graph store | Neo4j (story chains + topic graph) |
| Frontend | React + Vite + D3 |
| Sources | one news API (NewsAPI or GNews — TBD), arXiv API, GitHub API |
| Deployment | Docker (docker-compose.yml present at root) |

## 5. Story-Matching Decision Rules (from LLD §1.4 / §2.2-B)

| Semantic similarity | Time gap | Classification |
|---|---|---|
| > 0.92 | < 48 h | Duplicate / merge |
| > 0.75 | any | Attach as new chapter |
| 0.6 – 0.75 | weeks+ | **ASK_AGENT** (LangGraph reasoning node) — phase 2; initial fallback: treat as CREATE_NEW_STORY |
| < 0.6 | — | Create new story |

Story centroid update (incremental):
`new_centroid = old_centroid + (new_vec - old_centroid) / item_count`

## 6. Data Model Reference

**Postgres — `items`:** id (UUID PK), source_type (`news`/`paper`/`tool`),
source_name, external_id, title, raw_text, url, published_at, ingested_at,
story_id (FK→stories, nullable), summary, tags (text[]).

**Postgres — `stories`:** id (UUID PK), title, status (`active`/`dormant`/`resolved`),
first_seen_at, last_updated_at, centroid_embedding_id, item_count (denormalized).

**Chroma:** `item_vectors` (id=item.id, metadata {story_id, published_at});
`story_centroids` (id=story.id, running mean vector).

**Neo4j:**
```cypher
(:Story {id, title, status})
(:Item {id, title, published_at})
(:Topic {name})
(:Story)-[:HAS_CHAPTER {sequence: int}]->(:Item)
(:Item)-[:FOLLOWS {gap_hours: float}]->(:Item)
(:Item)-[:ABOUT]->(:Topic)
```

## 7. API Contracts (from LLD §2.3)

| Endpoint | Method | Returns |
|---|---|---|
| `/feed` | GET | Paginated items newest-first, each with `story_id` + `story_title` |
| `/stories` | GET | Active stories sorted by `last_updated_at`, with `item_count` |
| `/stories/{id}/timeline` | GET | Ordered chapters (title, summary, published_at) |
| `/topics/{name}/graph` | GET | Neo4j topic subgraph for graph explorer |

## 8. Repo Structure

```
backend/
  app/
    main.py            # FastAPI entry
    agents/            # LangGraph agent(s) — phase 2
    api/               # FastAPI routers
    chronology/        # Story matching / chronology subsystem (core deliverable)
    core/              # config, settings, logging
    db/                # Postgres models + session
    graph/             # Neo4j client/queries
    ingestion/         # pollers (news API, arXiv, GitHub)
    processing/        # normalize, dedup, embed, summarize
    schemas/           # Pydantic schemas
  tests/               # test_ingestion, test_dedup, test_chronology (stubbed)
frontend/
  src/{api, components, pages}   # Feed view, Timeline view (new), Graph explorer
scripts/
  seed_topics.py
docs/                  # proposal + HLD/LLD (see §2)
docker-compose.yml
```

## 9. Non-Functional Requirements

- **Extensibility:** don't hardcode the single-source assumption —
  `items.source_name` stays a text field.
- **Idempotency:** re-running a poller on overlapping windows must not create
  duplicate stories.
- **Explainability:** log every story-matching decision (why item X was attached
  to story Y) — most likely thing to need debugging/demo explanation.

## 10. Build Order (from LLD §2.6)

1. [ ] Single-source ingestion poller + Postgres `items` table (no story logic)
2. [ ] Exact dedup (canonical URL hash)
3. [ ] `stories` table + centroid matching with fixed thresholds
       (ambiguous band → fallback `CREATE_NEW_STORY`)
4. [ ] `/stories/{id}/timeline` + Timeline UI end-to-end — **demoable milestone**
5. [ ] LangGraph ambiguous-band reasoning agent
6. [ ] Neo4j topic graph + graph explorer

## 11. Progress Tracker

> Update this section at the end of every session.

- **Current step:** Not started — skeleton folders exist, no implementation yet.
- **Last session (2026-09-15):** Read docs, created this AGENTS.md.

## 12. Decisions & Open Questions

- [ ] **Open:** which news API — NewsAPI vs GNews (affects only poller
      request/response parsing, not the design).
- [ ] Embedding model choice (not specified in docs).
- [ ] LLM provider: proposal says Claude API (Anthropic); confirm what's available.
- [ ] Timezone/cursor strategy for poll windows.

## 13. Conventions

- Follow existing code style; minimal, focused changes.
- Tests live in `backend/tests/` mirroring subsystem names.
- Env config via `backend/.env` (see `.env.example`).
