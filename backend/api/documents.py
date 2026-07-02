from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from backend.ingestion.pipeline import list_documents, get_document
from backend.models.schemas import DocumentMetadata

router = APIRouter()


@router.get("/documents", response_model=list[DocumentMetadata])
async def get_documents():
    return list_documents()


@router.get("/documents/{doc_id}", response_model=DocumentMetadata)
async def get_document_metadata(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(
        path=str(file_path),
        filename=doc.name,
        media_type="application/octet-stream",
    )
