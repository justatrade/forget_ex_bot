from fastapi import APIRouter, UploadFile, File, Form
from pathlib import Path
import uuid

from api.services.insult_service import InsultService
from shared.database.models import GenderEnum

router = APIRouter(prefix="/api/insults", tags=["Insults"])


@router.post("/upload")
async def upload_insult_with_media(
    gender: GenderEnum = Form(...),
    text: str = Form(...),
    media: UploadFile = File(None)
):
    media_path = None
    media_type = None

    if media:
        ext = Path(media.filename).suffix
        filename = f"{uuid.uuid4()}{ext}"

        save_path = Path(f"media/insults/{gender.value}/{filename}")
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            content = await media.read()
            f.write(content)

        media_path = str(save_path)
        media_type = "photo" if ext in [".jpg", ".png", ".jpeg"] else "video"

    await InsultService.create_insult(gender.value, text, media_type, media_path)

    return {"status": "ok", "media_path": media_path}