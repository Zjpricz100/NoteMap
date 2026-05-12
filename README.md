# NoteMap

<img width="400" height="400" alt="image" src="https://github.com/user-attachments/assets/d9c0fc8a-9c12-404a-9cbb-e5c2f050f033" />


A personal knowledge map that transforms scattered notes into a navigable, clustered graph. Inspired by the Path of Exile skill tree, but for your own ML/engineering/domain knowledge.

## What it does

NoteMap ingests raw notes (handwritten PDFs, code files), embeds the content, clusters it into topic nodes, and renders a visual graph showing how your knowledge fits together.

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



