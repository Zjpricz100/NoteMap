from openai import OpenAI
from notemap.embeddings.chunking import Chunk, load_documents, chunks_from_pdf, chunks_from_code
from notemap.models import PDFDocument
from notemap.cache import content_hash, cache_path
import numpy as np
import json
from pathlib import Path

DEFAULT_MODEL = "text-embedding-3-small"
BATCH_SIZE = 256
MANIFEST_PATH = Path(__file__).resolve().parents[2] / "data" / "embeddings" / "manifest.json"

def chunks_to_embeddings(
        chunks : list[Chunk], 
        data_dir: Path, 
        client: OpenAI,
        model=DEFAULT_MODEL,
        batch_size=BATCH_SIZE) -> tuple[np.ndarray, list[str]]: # (chunk_id, embeddings)
    """
    Processes the text from a batch of chunks to create a batch of embeddings.

    Returns a np array of the embeddings and a list of chunk ids in the same order.
    """
    embeddings_dir = data_dir / "embeddings"
    embeddings_dir.mkdir(parents=True, exist_ok=True)

    cached_results = {}
    uncached_chunks = []

    for chunk in chunks:
        chunk_hash = chunk.chunk_id
        chunk_path = cache_path(data_dir, "embeddings", chunk_hash, ".npy")
        if chunk_path.exists():
            cached_results[chunk_hash] = np.load(chunk_path)
        else:
            uncached_chunks.append(chunk)

    for i in range(0, len(uncached_chunks), batch_size):
        batch = uncached_chunks[i : i + batch_size]
        response = client.embeddings.create(
            input=[c.text for c in batch],
            model=model
        )

        for chunk, item in zip(batch, response.data):
            embedding = np.array(item.embedding)
            chunk_hash = chunk.chunk_id
            chunk_path = cache_path(data_dir, "embeddings", chunk_hash, ".npy")
            np.save(chunk_path, embedding) # save the embedding locally for caching
            cached_results[chunk_hash] = embedding # load into our resulting cache our new embedding

    embeddings = np.array([cached_results[c.chunk_id] for c in chunks])
    chunk_ids = [c.chunk_id for c in chunks]
    assert(len(embeddings) == len(chunk_ids))
    return embeddings, chunk_ids




def load_pdf_embeddings(data_dir: Path, client: OpenAI, model=DEFAULT_MODEL, batch_size=BATCH_SIZE) -> tuple[np.ndarray, list[str]]:
    """Loads all embeddings and chunk_ids in data_dir. Order is preserved. Writes manifest.json as a side-effect."""
    documents = load_documents(data_dir / "documents")
    chunks = []
    for doc in documents:
        chunks.extend(chunks_from_pdf(doc))

    chunks = list({c.chunk_id : c for c in chunks}.values())
    embeddings, chunk_ids = chunks_to_embeddings(chunks, data_dir, client, model, batch_size)

    manifest = {}
    manifest_path = data_dir / MANIFEST_PATH

    chunk_data = [{
            "chunk_id": c.chunk_id, 
            "source_path": str(c.source_path), 
            "page_number": c.page_number,
            "x": None, # filled
            "y": None
        }
        for c in chunks
    ]
    manifest["chunks"] = chunk_data

    manifest_path.write_text(json.dumps(manifest))

    return embeddings, chunk_ids

    