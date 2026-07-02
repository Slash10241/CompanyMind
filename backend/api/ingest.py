import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.config import settings
from backend.ingestion.pipeline import ingest_file
from backend.models.schemas import IngestionResult

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".md"}


@router.post("/ingest", response_model=list[IngestionResult])
async def ingest_documents(files: list[UploadFile] = File(...)):
    results = []
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    for upload in files:
        suffix = Path(upload.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{suffix}' not supported. Allowed: {ALLOWED_EXTENSIONS}"
            )
        dest = uploads_dir / upload.filename
        # Handle filename collisions
        counter = 1
        while dest.exists():
            stem = Path(upload.filename).stem
            dest = uploads_dir / f"{stem}_{counter}{suffix}"
            counter += 1

        with dest.open("wb") as f:
            shutil.copyfileobj(upload.file, f)

        result = await ingest_file(str(dest), upload.filename)
        results.append(result)

    return results
