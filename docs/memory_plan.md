# Memory for Agent Orchestration — Design & Plan

Goal: add a memory subsystem to the agent orchestration (Crew) with explicit, controllable size limits. The memory should be pluggable, testable, and support typical retrieval patterns used by agents (recent context, semantic retrieval, and filtered recall).

## Short contract (2–4 bullets)

- Inputs: messages/observations, optional metadata (source, timestamp, agent id), and explicit size control parameters (max_tokens, max_items, time_window).
- Outputs: deterministic retrieval APIs: `get_recent(n_items)`, `get_semantic(query, k)`, `get_by_filter(filter_expr)`, and `summary()`.
- Error modes: storage backend unavailable, quota exceeded, invalid size config.
- Success criteria: memory honors size constraints under steady and burst writes and returns expected retrieval results in unit tests.

## Requirements

Must-have
- Ability to set and enforce size limits (by tokens, by item count, or by vector count).
- LRU or time-window eviction policy; support for TTL per item.
- Simple semantic search support (via embeddings) and exact/recency search.
- In-memory backend for local dev and persistent backend option (SQLite/Redis/Vector DB) for production.
- Clear API for the orchestration layer (`Crew`) to add, query, and remove memory items.

Nice-to-have
- Automatic summarization to compress old memory when size limits hit (summarize-and-replace strategy).
- Hybrid controls (token budget shared between conversation and memory).
- Metrics/logging for memory evictions and hit rates.

## Memory model (data shape)

A memory item (Python dataclass):

- id: str (uuid)
- text: str
- embedding: Optional[List[float]] (if semantic)
- tokens_estimate: int (approx tokens used)
- metadata: dict (source, timestamp, author, tags)
- created_at: datetime

## Backends

1. In-memory store
   - Simple Python list/dict + optional FAISS-like vector index in-memory.
   - Good for tests and single-process dev.

2. SQLite (with FTS)
   - Lightweight persistent storage and search.

3. Redis (with modules or sorted sets) or Redis + vector plugin
   - For low-latency multi-process use.

4. Vector DB (Pinecone/Weaviate/Chroma)
   - For scale and production semantic search.

Backend interface (abstract class / protocol):
- add(item)
- add_many(items)
- query_semantic(query_embedding, k)
- query_recent(k)
- delete(id)
- prune(policy_state)
- stats()

## Size-control strategies

Expose a configuration object to control memory size; allowed fields:
- max_items: int | None
- max_tokens: int | None
- max_embeddings: int | None
- time_window_seconds: int | None
- eviction_policy: enum {LRU, FIFO, TTL, REVERSE_CHRONO}
- summarize_on_eviction: bool

Eviction approaches
- Count-based eviction: maintain item count; remove oldest (or LRU) until under limit.
- Token-based eviction: maintain running sum of tokens_estimate; evict until under token budget.
- Vector-count enforced on vector DB (k-nearest stored vectors) — delete oldest vectors.
- Time-window eviction: remove items older than N seconds.

Advanced: compressed memory
- When eviction is triggered, instead of deleting oldest items, run a summarizer to compress multiple old items into a single summary item with a new token count. This preserves information within budget.

## Integration with Crew (API design)

Add a `memory` attribute to `Crew` (composition):

- crew.memory.add(text, metadata={}) -> item_id
- crew.memory.mget_recent(n)
- crew.memory.search(query_text, k, semantic=True)
- crew.memory.configure(size_config)
- crew.memory.prune()

Example usage in orchestration loop:

- On each observation: `crew.memory.add(obs_text, metadata)`
- Before calling model: fetch context `context_items = crew.memory.get_context(query, max_tokens=budget)`
- After model response: optionally `crew.memory.add(model_reply)`

## Size-control API examples

- `Memory.configure(max_tokens=2000, eviction_policy='token_lru')`
- `context = memory.get_context_for_prompt(prompt_tokens_left=1024)` — returns items packed to not exceed the token budget.

Packing algorithm (greedy)
- Sort candidate items by recency/score
- Keep adding until tokens + new_context_tokens > budget; return packed list.

## Tests to add

Unit tests
- Add/remove items and verify counts and tokens accounting.
- Eviction tests: set tiny `max_items`/`max_tokens`, write many items, and assert oldest/lowest-priority items are removed.
- Summarize-on-eviction test: when enabled, ensure multiple items replaced by one summary item.
- Query tests: semantic search returns expected top-k (can stub embeddings).

Integration tests
- End-to-end orchestration with memory: simulate a conversation, ensure context passed to the model is within token budget.
- Backend failure test: simulate backend unavailable and ensure graceful errors.

## Edge cases and considerations

- Token estimation: use a fast approximate token estimator (e.g., tiktoken or rough heuristics) to avoid heavy cost.
- Concurrency: if multiple workers share the same memory, prefer a central store (Redis/vector DB) and implement optimistic locking or atomic eviction operations.
- Cost: storing large text + embeddings increases storage; use compression or summarization for long-lived items.
- Privacy: ensure sensitive data in memory is redactable and that retention policies comply with requirements.

## Prototype plan (phases & timeline)

Phase 1 — Prototype (1–2 days)
- Implement `Memory` interface + in-memory backend.
- Add `max_items` and LRU eviction.
- Wire `Crew` to call `memory.add()` and `memory.get_recent()`.
- Add unit tests for eviction and basic retrieval.

Phase 2 — Semantic retrieval & token budgets (2–3 days)
- Add optional embedding generation hook (pluggable) and simple vector index using `numpy` + cosine similarity.
- Implement `max_tokens` eviction and `get_context_for_prompt()` packing by tokens.
- Add unit tests with stubbed embeddings and token counts.

Phase 3 — Persistent backends & summarization (3–5 days)
- Add SQLite and Redis adapters.
- Implement summarize-on-evict using a provided summarizer callback.
- Add integration tests and benchmarks.

Phase 4 — Hardening (ongoing)
- Add metrics (eviction counts, hit rate), logging, and TTL cleaning job.
- Add docs/examples and CLI flags to manage memory config.

## Minimal implementation checklist (first PR)

- [ ] `src/crew_ai/memory.py` — `Memory` interface and `MemoryItem` dataclass
- [ ] `src/crew_ai/backends/in_memory.py` — in-memory backend with LRU and count-based eviction
- [ ] `src/crew_ai/crew.py` — wire `Crew` to accept a `Memory` instance
- [ ] tests: `tests/test_memory.py` with eviction and retrieval tests
- [ ] docs: `docs/memory_plan.md` (this file)

## Recommended concrete stack (your choices)

Short-term memory (current context)
- Backend: ChromaDB (local or hosted) used for RAG-style retrieval of recent context and fast semantic search.
- Use it for immediate conversation context and for fast semantic nearest-neighbor recall.

Long-term memory (cross-session persistence)
- Backend: SQLite3 database file to store task results, summaries, and long-lived structured records.
- Keep a single `long_term_memory_storage.db` in the project storage location and expose simple query APIs for analytic retrieval.

Entity memory
- Use RAG (embeddings + vector search) to index and retrieve entity-focused records (people, places, concepts).
- Store canonical entity metadata in SQLite and embed textual descriptions into Chroma for semantic lookup.

Storage location and layout
- Use the `appdirs` package to determine a platform-specific project storage base, but allow overriding with an environment variable `CREWAI_STORAGE_DIR`.
- Example directory layout (per-project):

```
~/.local/share/CrewAI/{project_name}/
├── knowledge/
├── short_term_memory/        # ChromaDB local DB files or directory
├── long_term_memory/         # optional files related to long-term storage
├── entities/                 # entity-specific artifacts and indexes
└── long_term_memory_storage.db
```

Implementation notes
- On startup, compute storage dir as:

```python
from appdirs import user_data_dir
import os

storage_dir = os.environ.get("CREWAI_STORAGE_DIR")
if not storage_dir:
   storage_dir = user_data_dir("CrewAI", "your_org")

# project-specific path
project_storage = os.path.join(storage_dir, project_name)
os.makedirs(project_storage, exist_ok=True)
```

- Place ChromaDB files under `short_term_memory/` and the SQLite DB under `long_term_memory_storage.db` at the top level.

Crew initialization example (Azure OpenAI embedder + memory enabled)

```python
crew = Crew(
   memory=True,
   embedder={
      "provider": "openai",  # Use openai provider for Azure
      "config": {
         "api_key": "your-azure-api-key",
         "api_base": "https://your-resource.openai.azure.com/",
         "api_type": "azure",
         "api_version": "2023-05-15",
         "model_name": "text-embedding-3-small",
         "deployment_id": "your-deployment-name"  # Azure deployment name
      }
   }
)
```

How components map to the Memory API
- Short-term RAG: use Chroma for `memory.search(query, k, semantic=True)` and for fast context packing.
- Long-term store: write task results and summaries to SQLite; implement a background job to periodically summarize older short-term items into long-term SQLite entries.
- Entities: maintain an `entities` table in SQLite (id, canonical_name, metadata) and index descriptive text into Chroma for entity RAG queries.

Notes on deployment and operations
- Chroma local stores can be heavy on disk and should be persisted in the project storage directory.
- SQLite is portable but for multi-process access consider WAL mode and appropriate locks; for multi-host production use a proper database (Postgres) instead.
- Provide a small CLI or management utilities to inspect and compact memory folders.

Next steps to implement the concrete stack in Phase 1/2
- Add `src/crew_ai/backends/chroma_backend.py` adapter that wraps Chroma operations (init, add, query, delete).
- Add `src/crew_ai/backends/sqlite_backend.py` for long-term storage and entities table.
- In `Crew`, add configuration to point to `project_storage` and initialize Chroma with the `short_term_memory` folder.
- Add tests that use a temporary directory (pytest tmp_path) and validate short-term RAG + long-term persistence.

## Quality gates

- Build: ensure project imports cleanly.
- Unit tests: at least 5 unit tests covering happy path, eviction, token packing, and failure.
- Performance smoke: inserting 10k lightweight items in-memory should not crash (duration tolerance depending on CI).

## Verification / smoke commands

```bash
# run unit tests
pytest tests/test_memory.py -q

# run a small local script that demonstrates adding and retrieving
python - <<'PY'
from crew_ai.backends.in_memory import InMemoryBackend
from crew_ai.memory import Memory
m = Memory(InMemoryBackend(max_items=5))
for i in range(10):
    m.add(f"note {i}")
print(m.get_recent(5))
PY
```

## Next steps for me

1. Implement the `Memory` interface and in-memory backend as a first PR.
2. Add unit tests for eviction and context packing.
3. Iterate on token-based eviction and summarization.

---

If you'd like, I can now implement the Phase 1 prototype (`src/crew_ai/memory.py` and an in-memory backend) and add tests; tell me to proceed and I'll: create the files, run tests locally, and iterate until green.
