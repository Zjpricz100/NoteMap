from pydantic import BaseModel
from pathlib import Path
from notemap.models import PDFDocument, CodeSummary
from notemap.cache import content_hash

class Chunk(BaseModel):
    chunk_id : str
    source_path : Path
    source_type: str # "pdf_page", "code_chunk"
    page_number: int | None # None for pdfs for now
    text: str # The actual content of the chunk
    summary: str # 3-5 word summary of the content of this chunk
    image_hash: str # hash to the source image
    

def chunks_from_pdf(doc : PDFDocument) -> list[Chunk]:
    """Creates chunks from a pdf. By default, one page from a pdf will map to one chunk."""
    chunks = []
    for page_num, page in enumerate(doc.pages):
        chunks.append(Chunk(
            chunk_id=content_hash(page.transcription.encode()),
            source_path=doc.source_path,
            source_type="pdf_page",
            page_number=page_num + 1,
            text=page.transcription,
            summary=page.summary,
            image_hash=page.image_hash
        ))
    return chunks

def chunks_from_code(doc: CodeSummary) -> list[Chunk]:
    pass


def load_documents(json_dir: Path) -> list[PDFDocument]:
    
    """Loads a list of documents from a json directory path."""
    return [
        PDFDocument.model_validate_json(path.read_text())
        for path in Path(json_dir).glob("*.json")
    ]
