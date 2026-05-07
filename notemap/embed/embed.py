from openai import OpenAI
from notemap.embed.chunking import Chunk, load_documents, chunks_from_pdf, chunks_from_code
from notemap.models import PDFDocument
import numpy as np

DEFAULT_MODEL = "text-embedding-3-small"

def chunks_to_embeddings(chunks : list[Chunk], batch_size=256, client=OpenAI, model=DEFAULT_MODEL) -> np.array:
    """Processes the text from a batch of chunks to create a batch of embeddings"""
    embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        response = client.embeddings.create(
            input=batch,
            model=model
        )
        embeddings.extend(item.embedding for item in response.data)
    return np.array(embeddings)


def pdfs_to_embeddings(pdfs: list[PDFDocument], batch_size=256, client=OpenAI, model=DEFAULT_MODEL) -> list[np.array]:
    """Processes a list of pdfs """
    pdf_embeddings = []
    for pdf_doc in pdfs:
        pdf_chunks = chunks_from_pdf(pdf_doc)
        doc_embeddings = chunks_to_embeddings(pdf_chunks, batch_size=batch_size, client=client, model=model)
        pdf_embeddings.append(doc_embeddings)
    return np.array(pdf_embeddings)
