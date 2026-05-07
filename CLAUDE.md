# CLAUDE.md — NoteMap Working Reference

This file is my (Claude's) persistent working context for the NoteMap project. I update it as we build. Read this at the start of every session.

---

## Project in one sentence

Transform scattered notes (handwritten PDFs, code files) into a clustered, visual knowledge graph.

---

## Pipeline stages

```
[Raw files]
    │
    ▼
1. Ingest        — rasterize PDFs → vision LLM → markdown; tree-sitter → LLM summary
    │
    ▼
2. Store         — Pydantic models (Page, Document); local FS + PNG images; content-hash cache
    │
    ▼
3. Embed         — chunk content → OpenAI text-embedding-3-large; batch + cache by text hash
    │
    ▼
4. Cluster       — UMAP (→ ~10D) → HDBSCAN; LLM labels from 10-NN chunks per cluster
    │
    ▼
5. Visualize     — UMAP (→ 2D) → scatter plot (matplotlib/plotly), colored by cluster
```

---

## Current focus

**Stage: Not started — foundation files created, no pipeline code written yet.**

Next step pending user approval: scaffold the directory layout and then begin Stage 1 (Ingestion).

---

## Current state

| Stage | Status | Notes |
|---|---|---|
| Project foundation | Done | README.md + CLAUDE.md created |
| Directory layout | Proposed (not created) | See below — awaiting approval |
| Ingestion | Not started | |
| Storage / schemas | Not started | |
| Embedding | Not started | |
| Clustering | Not started | |
| Visualization | Not started | |

---

## Proposed directory layout

```
NoteMap/
├── README.md
├── CLAUDE.md
├── pyproject.toml          # deps + entry points
├── .env.example            # API keys template
│
├── notes/                  # drop raw input files here
│   ├── pdfs/
│   └── code/
│
├── data/                   # all generated/cached artifacts (gitignored)
│   ├── pages/              # per-page PNG images
│   ├── transcriptions/     # markdown outputs, keyed by content hash
│   ├── summaries/          # LLM code summaries, keyed by content hash
│   ├── embeddings/         # numpy arrays or parquet, keyed by text hash
│   └── clusters/           # UMAP coords + HDBSCAN labels
│
├── notemap/                # source package
│   ├── __init__.py
│   ├── models.py           # Pydantic schemas (Page, Document, Chunk, …)
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── pdf.py          # rasterize + vision LLM transcription
│   │   └── code.py         # tree-sitter parse + LLM summary
│   ├── embed.py            # chunking + OpenAI embedding + cache
│   ├── cluster.py          # UMAP + HDBSCAN + LLM labels
│   └── visualize.py        # 2D UMAP + scatter plot
│
└── scripts/                # one-off CLI entry points (thin wrappers)
    ├── ingest.py
    ├── embed.py
    ├── cluster.py
    └── visualize.py
```

**Rationale for key decisions:**
- `notemap/` is a proper package so stages can import each other's models cleanly.
- `data/` is fully gitignored — everything in it is reproducible from the raw `notes/`.
- `scripts/` are thin wrappers; logic lives in `notemap/` so it's testable.
- Stage boundaries are in separate modules so implementations can be swapped without touching downstream code.

---

## Stack decisions

| Concern | Decision | Reason |
|---|---|---|
| Schemas | Pydantic | Validation + serialization; easy to evolve |
| PDF rasterization | pdf2image / pymupdf | TBD at implementation time |
| Transcription LLM | Claude or GPT-4o | Vision quality; decide at impl time |
| Code parsing | tree-sitter | Language-agnostic AST without running code |
| Embeddings | OpenAI text-embedding-3-large | Best quality/cost for semantic chunking |
| Dimensionality reduction | umap-learn | Preserves local + global structure |
| Clustering | hdbscan | Handles variable-density clusters; no fixed k |
| Storage | Local filesystem | Simple; no infra; SQLite only if obviously needed |
| Visualization | matplotlib or plotly | Fastest path to sanity-checking clusters |

---

## Caching contract

Every expensive operation must be skippable on re-run:
- **LLM transcriptions**: keyed by SHA-256 of the source page image bytes
- **LLM summaries**: keyed by SHA-256 of the source file content
- **Embeddings**: keyed by SHA-256 of the chunk text
- Cache miss → call API → write result. Cache hit → load and return. No exceptions.

---

## Working style

- **One step at a time.** Don't scaffold the whole pipeline at once.
- **Explain tradeoffs, not trivia.** Call out real design choices; skip narrating obvious steps.
- **Clean stage interfaces.** Each stage reads from the previous stage's output format. Swapping an implementation shouldn't require touching downstream code.
- **Minimal scope.** Don't build deferred features. Don't add abstractions for hypothetical future needs.

---

## Deferred — do not build until asked

- Edge construction between nodes/clusters
- Semantic search layer
- "Project advisor" mode (feed project description → get relevant clusters)
- Frontend polish: Sigma.js, hover viewers, PDF.js, Monaco editor
- Dropbox / Google Drive / iPad sync
- DVC pipeline orchestration
- Vector DB (numpy/parquet is sufficient)
- MLflow, vLLM, LangChain
- Placeholder node generation for unfamiliar tech

---

## Open questions / decisions pending

- PDF rasterization library: `pdf2image` (poppler-based) vs `pymupdf` — decide when starting Stage 1.
- Transcription LLM: Claude claude-sonnet-4-6 vs GPT-4o — compare quality/cost at Stage 1.
- SQLite vs flat JSON for document index — defer until storage needs become clear.
- Chunking strategy for embedding: fixed-size vs sentence-boundary vs semantic — decide at Stage 3.
