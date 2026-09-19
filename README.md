# AI News Agent — Team Chronologix

> **Design driver:** *"Bridge the gap in the chronology of news — how news is progressing."*  
> Given a stream of individually-published articles, reconstruct the **evolving storylines** they belong to and present each storyline as an ordered **timeline**, not a flat feed.

---

## 1. Project Summary

The AI News Agent ingests AI-specific news (single source: GNews), research papers (arXiv), and tool releases (GitHub), then turns them into short, sourced summaries organized into **Stories** — evolving storylines shown as chronological timelines.

This is a **prototype** (scope reduced from the original multi-source proposal) focused on the **Chronology subsystem** as the core deliverable.

---

## 2. Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Agent orchestration | LangGraph (phase 2: ambiguous-band story-matching) |
| Relational DB | PostgreSQL 16 (`items`, `stories`, `poll_cursors`) |
| Vector store | Chroma (local `item_vectors`, `story_centroids`) |
| Graph store | Neo4j 5 (story chains + topic graph) |
| Frontend | React 18 + Vite + D3.js |
| Scheduling | In-process cron (dev) / cron or Airflow (prod) |
| Deployment | Docker Compose (see `docker-compose.yml`) |

---

## 3. Key Architectural Decisions

### 3.1 Story Entity (First-Class Chronology)
Every ingested item is classified into exactly one of three outcomes:
1. **Duplicate** — same event, different phrasing/outlet (merge / skip)
2. **New chapter** — later development in an existing storyline (attach to Story)
3. **New story** — nothing similar exists yet (create new Story)

Classification uses **semantic similarity** + **temporal gap**:

| Similarity | Time gap | Action |
|------------|----------|--------|
| > 0.92 | < 48 h | Duplicate / merge |
| > 0.75 | any | Attach as new chapter |
| 0.6 – 0.75 | weeks+ | **ASK_AGENT** (LangGraph reasoning node — phase 2; fallback: `CREATE_NEW_STORY`) |
| < 0.6 | — | Create new story |

### 3.2 Story Centroid (Incremental)
Story centroid embedding is a running mean of member item vectors:
```python
new_centroid = old_centroid + (new_vec - old_centroid) / item_count
```
Stored in Chroma collection `story_centroids` (key = story.id).

### 3.3 Neo4j Graph Model
```cypher
(:Story {id, title, status})
(:Item {id, title, published_at})
(:Topic {name})

(:Story)-[:HAS_CHAPTER {sequence: int}]->(:Item)
(:Item)-[:FOLLOWS {gap_hours: float}]->(:Item)  // chronological chain within a story
(:Item)-[:ABOUT]->(:Topic)
```
Timeline reconstruction = single `MATCH ... ORDER BY published_at` traversal.

### 3.4 Non-Functional Requirements
- **Extensibility:** `items.source_name` is free text (not enum) — adding a second news API requires no migration.
- **Idempotency:** Re-running a poller on overlapping windows must not create duplicate stories (exact dedup via `external_id` unique key + PollCursor).
- **Explainability:** Every story-matching decision is logged (why item X attached to story Y).

---

## 4. Data Model (PostgreSQL)

### `items`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| source_type | TEXT | `news` / `paper` / `tool` |
| source_name | TEXT | e.g. `"gnews"` — free text for extensibility |
| external_id | TEXT UNIQUE | Canonical URL hash / arXiv ID / release tag |
| title | TEXT | |
| raw_text | TEXT | |
| url | TEXT | Canonicalized (tracking params stripped) |
| published_at | TIMESTAMPTZ | From source |
| ingested_at | TIMESTAMPTZ | |
| story_id | UUID FK → stories.id | Nullable until matched |
| summary | TEXT | Filled at enrichment stage |
| tags | TEXT[] | Subfield tags |

### `stories`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| title | TEXT | Auto-generated from first item, editable |
| status | TEXT | `active` / `dormant` / `resolved` |
| first_seen_at | TIMESTAMPTZ | |
| last_updated_at | TIMESTAMPTZ | |
| centroid_embedding_id | TEXT | Pointer to Chroma story-centroid vector |
| item_count | INT | Denormalized for feed sorting |

### `poll_cursors`
| Column | Type | Notes |
|--------|------|-------|
| source | TEXT PK | e.g. `"gnews"`, `"arxiv"`, `"github"` |
| last_polled_at | TIMESTAMPTZ | Incremental cursor per source |

---

## 5. API Contracts

| Endpoint | Method | Returns |
|----------|--------|---------|
| `/feed` | GET | Paginated items newest-first, each with `story_id` + `story_title` |
| `/stories` | GET | Active stories sorted by `last_updated_at`, with `item_count` |
| `/stories/{id}/timeline` | GET | Ordered chapters (title, summary, published_at) |
| `/topics/{name}/graph` | GET | Neo4j topic subgraph for graph explorer |

---

## 6. Repository Structure

```
backend/
  app/
    main.py                    # FastAPI entry, wires routers
    core/
      config.py                # Pydantic Settings (env-driven)
      logging.py
    db/
      models.py                # SQLAlchemy models: Item, Story, PollCursor
      postgres.py              # Lazy engine + SessionLocal factory + init_db
      chroma_client.py         # Chroma collections (item_vectors, story_centroids)
    ingestion/
      normalizer.py            # URL canonicalization + per-source normalizers
      scheduler.py             # PollCursor get/set + DEFAULT_LOOKBACK
      pollers/
        news_poller.py         # GNews API poller (run() orchestrates fetch→dedup→insert)
        arxiv_poller.py        # (stub)
        github_poller.py       # (stub)
    processing/
      dedup.py                 # Exact dedup by external_id + batch insert
      embeddings.py            # (stub)
      classifier.py            # (stub)
      summarizer.py            # (stub)
    chronology/
      story_matcher.py         # Centroid query + threshold logic (step 3)
      centroid_store.py        # Incremental centroid update (step 3)
      agent_nodes.py           # LangGraph ambiguous-band node (phase 2)
    graph/
      neo4j_client.py          # Neo4j driver + session management
      queries.py               # Cypher queries for story/topic graph
    agents/
      graph_builder.py         # LangGraph agent assembly (phase 2)
    api/
      dependencies.py          # FastAPI deps: DB session, settings
      routes/
        feed.py                # GET /feed
        stories.py             # GET /stories, GET /stories/{id}/timeline
        topics.py              # GET /topics/{name}/graph
    schemas/
      item.py                  # Pydantic ItemOut
      story.py                 # Pydantic StoryOut
  tests/
    test_ingestion.py          # Normalizer, poller, dedup (SQLite in-memory)
    test_dedup.py              # (stub)
    test_chronology.py         # (stub)
frontend/
  src/
    api/client.js              # Axios wrapper + base URL
    components/
      Feed/FeedCard.jsx        # Feed item card with "Part of story →" link
      Timeline/Timeline.jsx    # Vertical chapter-by-chapter timeline
      GraphExplorer/GraphExplorer.jsx
    pages/
      FeedPage.jsx             # /feed list
      StoryPage.jsx            # /stories/:id timeline view
      GraphPage.jsx            # /topics/:name graph explorer
scripts/
  seed_topics.py               # One-off Neo4j topic seeding
docs/
  AI_News_Agent_HLD_LLD.md     # Authoritative design (HLD + LLD)
  AI_News_Agent_Proposal_v3 (1).pdf  # Original proposal (superseded where conflicting)
docker-compose.yml
AGENTS.md                      # Session context for AI agents
```

---

## 7. Build Order (from LLD §2.6)

| Step | Description | Status |
|------|-------------|--------|
| 1 | Single-source ingestion poller + Postgres `items` table (no story logic) | ✅ Done |
| 2 | Exact dedup (canonical URL hash) | ✅ Done (in `processing/dedup.py`) |
| 3 | `stories` table + centroid matching with fixed thresholds (ambiguous → `CREATE_NEW_STORY`) | ⬜ Next |
| 4 | `/stories/{id}/timeline` + Timeline UI end-to-end — **demoable milestone** | ⬜ |
| 5 | LangGraph ambiguous-band reasoning agent | ⬜ |
| 6 | Neo4j topic graph + graph explorer | ⬜ |

**Current branch:** `step1-gnews-ingestion`

---

## 8. Running Locally

### Prerequisites
- Docker + Docker Compose (for Postgres + Neo4j)
- Python 3.11+
- Node 18+ (for frontend)

### Environment Setup
```bash
# 1. Clone & enter
git clone https://github.com/23f2003657/NEWS-AGENT.git
cd NEWS-AGENT

# 2. Configure backend env
cp backend/.env.example backend/.env
# Edit backend/.env with your GNews API key:
# NEWS_API_KEY=your_gnews_key
# NEWS_QUERY=artificial intelligence
# POSTGRES_URL=postgresql://user:pass@localhost:5432/ai_news_agent
# NEO4J_URI=bolt://localhost:7687
# CHROMA_PATH=./chroma_data

# 3. Start databases
docker compose up -d postgres neo4j

# 4. Backend (venv)
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Initialize tables
python -c "from app.db.postgres import init_db; init_db()"

# 5. Run a one-off poll (tests ingestion end-to-end)
python -m app.ingestion.pollers.news_poller

# 6. Start API server
uvicorn app.main:app --reload --port 8000

# 7. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
```

### Run Tests (backend)
```bash
cd backend
source .venv/bin/activate
pytest tests -q
# 4 passing: canonicalize_url, normalize_gnews, poll idempotency, cursor roundtrip
```

---

## 9. Key Files to Understand the Ingestion Flow

1. **`backend/app/ingestion/pollers/news_poller.py`** — Entry point: `run()` calls `fetch_new_items()` → `insert_new_items()` → updates cursor.
2. **`backend/app/ingestion/normalizer.py`** — `canonicalize_url()`, `url_hash()`, `normalize_gnews()`.
3. **`backend/app/processing/dedup.py`** — `is_exact_duplicate()`, `insert_new_items()` (batch fetch existing IDs, skip duplicates).
4. **`backend/app/ingestion/scheduler.py`** — `get_last_poll_timestamp()`, `set_last_poll_timestamp()` (PollCursor table).
5. **`backend/app/db/models.py`** — SQLAlchemy models with dialect-agnostic types (UUID/ARRAY variants for SQLite tests).
6. **`backend/app/db/postgres.py`** — Lazy engine (`@lru_cache`) so tests can monkeypatch `SessionLocal` without import-time failures.

---

## 10. Open Decisions (from AGENTS.md)

- [ ] **News API choice** — Currently GNews; could swap to NewsAPI by replacing `news_poller.py` fetch logic.
- [ ] **Embedding model** — Not specified; decision needed before step 3 (centroid matching).
- [ ] **LLM provider** — Proposal says Claude API (Anthropic); confirm availability.
- [ ] **Timezone/cursor strategy** — Poll windows currently use UTC; confirm if source APIs require different handling.

---

## 11. Session Context (AGENTS.md)

For AI agents picking up work: see **`AGENTS.md`** at repo root — it contains the authoritative project summary, data models, thresholds, build order checklist, progress tracker, and open questions. Update it at the end of every session.

---

## 12. License

Internal prototype — Team Chronologix.