import base64
import tempfile
from pathlib import Path
import os

import fitz  # pymupdf
from anthropic import Anthropic

from notemap.cache import cache_path, content_hash
from notemap.models import PageTranscription, PDFDocument

DPI = 150
DEFAULT_MODEL = "claude-sonnet-4-6"
TRANSCRIPTION_PROMPT = (
    "Transcribe exactly what is handwritten or printed on this page to markdown. "
    "Preserve structure, headings, lists, equations, and diagrams as faithfully as possible "
    "using markdown conventions. Output only the transcription — no commentary."
)


def rasterize_pdf(pdf_path: Path) -> list[tuple[int, bytes]]:
    """Return [(page_number, png_bytes), ...] for every page in the PDF."""
    doc = fitz.open(str(pdf_path))
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pages = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pages.append((i, pix.tobytes("png")))
    doc.close()
    return pages


def transcribe_page(
    image_bytes: bytes,
    client: Anthropic,
    data_dir: Path,
    image_hash: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Return markdown transcription, using cache if available."""
    cached = cache_path(data_dir, "transcriptions", image_hash, ".md")
    if cached.exists():
        return cached.read_text(encoding="utf-8")

    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
                    {"type": "text", "text": TRANSCRIPTION_PROMPT},
                ],
            }
        ],
    )
    text = response.content[0].text

    # Atomic write: temp file → rename
    tmp = cached.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.rename(cached)

    return text


def ingest_pdf(pdf_path: Path, data_dir: Path, client: Anthropic, model: str = DEFAULT_MODEL) -> PDFDocument:
    """Rasterize + transcribe all pages; cache both PNGs and transcriptions."""
    pdf_bytes = pdf_path.read_bytes()
    file_hash = content_hash(pdf_bytes)

    pages_dir = data_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "transcriptions").mkdir(parents=True, exist_ok=True)

    raw_pages = rasterize_pdf(pdf_path)
    transcriptions: list[PageTranscription] = []

    for page_number, png_bytes in raw_pages:
        image_hash = content_hash(png_bytes)
        img_path = cache_path(data_dir, "pages", image_hash, ".png")

        if not img_path.exists():
            tmp = img_path.with_suffix(".tmp")
            tmp.write_bytes(png_bytes)
            tmp.rename(img_path)

        was_cached = cache_path(data_dir, "transcriptions", image_hash, ".md").exists()
        text = transcribe_page(png_bytes, client, data_dir, image_hash, model=model)

        transcriptions.append(
            PageTranscription(
                page_number=page_number,
                image_path=img_path,
                image_hash=image_hash,
                transcription=text,
            )
        )
        print(f"  page {page_number}: {'(cached)' if was_cached else 'transcribed'}")

    return PDFDocument(source_path=pdf_path, file_hash=file_hash, pages=transcriptions)

def save_pdfs(pdfs_dir: str, out_dir: str, client = Anthropic, model: str = DEFAULT_MODEL):
    """Rasterizes + transcribes all pdfs and all pages pdfs_path and stores their JSONs in out_dir"""
    input_path = Path(pdfs_dir)
    output_path = Path(out_dir)
    output_documents_path = output_path / "documents"
    
    output_documents_path.mkdir(parents=True, exist_ok=True)

    pdf_file_paths = input_path.rglob("*.pdf")
    for pdf_file_path in pdf_file_paths:
        stem = pdf_file_path.stem
        doc = ingest_pdf(pdf_file_path, output_path, client, model)
        doc_json = doc.model_dump_json(indent=2)
        pdf_file_out_path = output_documents_path / f"{stem}_{doc.file_hash[:8]}.json"
        pdf_file_out_path.write_text(doc_json)
        print("Ingested and saved JSON data for ", pdf_file_out_path)


        



