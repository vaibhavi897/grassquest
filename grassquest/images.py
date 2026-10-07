"""Image validation, resizing and local persistence helpers."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def prepare_image(data: bytes, max_side: int = 1024) -> tuple[bytes, str]:
    """Validate an image and return resized JPEG bytes and a brief error-safe format."""
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("Image is empty or larger than 15 MB.")
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format not in SUPPORTED_FORMATS:
                raise ValueError("Use a JPG, PNG or WEBP image.")
            image = image.convert("RGB")
            image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue(), image.format or "image"
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("This image could not be read. Try another JPG, PNG or WEBP file.") from exc


def save_photo(data: bytes, folder: Path, filename: str) -> Path:
    """Store a validated, resized photo below the local data folder."""
    encoded, _ = prepare_image(data)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"{filename}.jpg"
    target.write_bytes(encoded)
    return target
