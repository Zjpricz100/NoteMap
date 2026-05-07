from pathlib import Path
from pydantic import BaseModel


class PageTranscription(BaseModel):
    page_number: int
    image_path: Path       # data/pages/{hash}.png
    image_hash: str        # sha256 of PNG bytes
    transcription: str     # markdown from vision LLM


class PDFDocument(BaseModel):
    source_path: Path
    file_hash: str         # sha256 of original PDF bytes
    pages: list[PageTranscription]


class CodeSummary(BaseModel):
    source_path: Path
    file_hash: str         # sha256 of source file bytes
    language: str
    summary: str           # markdown from LLM


class IngestManifest(BaseModel):
    pdfs: list[PDFDocument] = []
    code_files: list[CodeSummary] = []
