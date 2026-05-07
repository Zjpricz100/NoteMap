# NoteMap

A personal knowledge map that transforms scattered notes into a navigable, clustered graph. Inspired by the Path of Exile skill tree, but for your own ML/engineering/domain knowledge.

## What it does

NoteMap ingests raw notes (handwritten PDFs, code files), embeds the content, clusters it into topic nodes, and renders a visual graph showing how your knowledge fits together.

## Current scope (v1 pipeline)

The first version builds the full pipeline from raw input to clustered embeddings with a basic visualization:

1. **Ingestion** — Handwritten PDFs are rasterized page-by-page and transcribed to markdown via a vision LLM. Code files are parsed with tree-sitter and summarized via LLM.
2. **Storage** — Pydantic models for `Page` / `Document` objects. Content and transcriptions persisted to local filesystem; page images stored as PNGs. Aggressive content-hash caching so LLM calls are never repeated unnecessarily.
3. **Embedding** — Parsed content is chunked and embedded with OpenAI `text-embedding-3-large`. Batch API calls; embeddings cached by text hash.
4. **Clustering** — UMAP reduces to ~10 dims, then HDBSCAN clusters the reduced space. Cluster labels generated via LLM from the 10 nearest-neighbor chunks to each cluster centroid.
5. **Visualization** — Second UMAP reduction to 2D for layout. Scatter plot colored by cluster with labels visible (matplotlib or plotly). The goal here is sanity-checking clusters, not polish.

## Deferred (not in v1)

- Edge construction between nodes/clusters
- Semantic search and "project advisor" mode
- Frontend polish (Sigma.js, hover viewers, PDF.js, Monaco)
- Dropbox/Google Drive/iPad sync — for now, drop files into a local folder
- DVC pipeline orchestration
- Vector DB (numpy/parquet is fine for now)
- MLflow, vLLM, LangChain

## Stack

| Concern | Choice |
|---|---|
| Language | Python |
| Schemas | Pydantic |
| PDF rasterization | `pdf2image` / `pymupdf` |
| Handwriting transcription | Vision LLM (Claude or GPT-4o) |
| Code parsing | tree-sitter |
| Embeddings | OpenAI `text-embedding-3-large` |
| Dimensionality reduction | `umap-learn` |
| Clustering | `hdbscan` |
| Storage | Local filesystem + optional SQLite |
| Visualization | matplotlib or plotly |



