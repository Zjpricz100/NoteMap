import base64
import json
import tempfile
from pathlib import Path
import os
import re

import fitz  # pymupdf
from anthropic import Anthropic

from notemap.cache import cache_path, content_hash
from notemap.models import PageTranscription, PDFDocument

DPI = 150
DEFAULT_MODEL = "claude-sonnet-4-6"

# Prompt for our model. We specify XML formatting for output so the LLM is able to easily attach its transcription.
TRANSCRIPTION_PROMPT = (
    "Transcribe exactly what is handwritten or printed on this page to markdown. "
    "Preserve structure, headings, lists, equations, and diagrams as faithfully as possible "
    "using markdown conventions. Additionally give a 3-5 word summary of that document.\n\n"
    "Respond in this exact format, with no other text before or after:\n\n"
    "<summary>3-5 word summary here</summary>\n"
    "<document>\n"
    "full markdown transcription here\n"
    "</document>"
)

def parse_response(text):
    summary_match = re.search(r'<summary>(.*?)</summary>', text, re.DOTALL)
    document_match = re.search(r'<document>(.*?)</document>', text, re.DOTALL)
    
    summary = summary_match.group(1).strip() if summary_match else "N/A"
    document = document_match.group(1).strip() if document_match else "N/A"
    
    return summary, document



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
    """Return (summary, transcription), using cache if available."""
    cached = cache_path(data_dir, "transcriptions", image_hash, ".json")
    if cached.exists():
        data = json.loads(cached.read_text(encoding="utf-8"))
        return data["summary"], data["transcription"]

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

    summary, transcription = parse_response(text)

    # Atomic write: temp file → rename
    tmp = cached.with_suffix(".tmp")
    tmp.write_text(json.dumps({"summary": summary, "transcription": transcription}), encoding="utf-8")
    tmp.rename(cached)

    return summary, transcription


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

        was_cached = cache_path(data_dir, "transcriptions", image_hash, ".json").exists()
        summary, transcription = transcribe_page(png_bytes, client, data_dir, image_hash, model=model)

        transcriptions.append(
            PageTranscription(
                page_number=page_number,
                image_path=img_path,
                image_hash=image_hash,
                transcription=transcription,
                summary=summary
            )
        )
        #print(f"  page {page_number}: {'(cached)' if was_cached else 'transcribed'}")

    return PDFDocument(source_path=pdf_path, file_hash=file_hash, pages=transcriptions)

def save_pdfs(pdfs_dir: Path, out_dir: Path, client = Anthropic, model: str = DEFAULT_MODEL):
    """Rasterizes + transcribes all pdfs and all pages pdfs_path and stores their JSONs in out_dir"""
    input_path = pdfs_dir
    output_path = out_dir
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


        



