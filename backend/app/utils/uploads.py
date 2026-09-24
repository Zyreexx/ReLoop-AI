"""
Upload processing and strict validation for image uploads.
Validates file type by content inspection (magic bytes), enforces file size limits,
and sanitizes filenames. Never logs image bytes.
"""
import re
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile
from app.config import settings
from app.errors import AppError, ErrorCode

ALLOWED_MAGIC_BYTES = [
    (b"\xff\xd8\xff", "image/jpeg", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", "image/png", ".png"),
    (b"RIFF", "image/webp", ".webp"),  # Sub-checked with WEBP at offset 8
]


class ProcessedImage:
    def __init__(self, filename: str, mime_type: str, data: bytes):
        self.filename = filename
        self.mime_type = mime_type
        self.data = data
        self.size_bytes = len(data)


def detect_image_type(header: bytes) -> Tuple[str, str]:
    """
    Detects image type strictly from magic bytes content, not filename.
    Returns (mime_type, extension) or raises AppError.
    """
    if len(header) < 12:
        raise AppError(
            code=ErrorCode.INVALID_INPUT.value,
            message="Uploaded file is too small or corrupted.",
            field="images",
            http_status=400,
        )

    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    elif header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    elif header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp", ".webp"

    raise AppError(
        code=ErrorCode.INVALID_INPUT.value,
        message="Unsupported image format. Allowed formats: JPEG, PNG, WebP.",
        field="images",
        http_status=400,
    )


def sanitize_filename(filename: str) -> str:
    """
    Strips directory traversal and illegal characters from filenames.
    """
    raw_name = Path(filename).name
    # Keep only alphanumeric, hyphens, underscores, dots
    cleaned = re.sub(r"[^\w\.\-]", "_", raw_name)
    return cleaned if cleaned else "image.jpg"


async def validate_and_process_upload_files(
    files: List[UploadFile],
    min_files: int = 1,
    max_files: int = 3,
) -> List[ProcessedImage]:
    """
    Validates uploaded multipart files for count, size, and real image magic bytes.
    """
    if not files or len(files) < min_files:
        raise AppError(
            code=ErrorCode.INVALID_INPUT.value,
            message=f"Please upload at least {min_files} image(s).",
            field="images",
            http_status=400,
        )

    if len(files) > max_files:
        raise AppError(
            code=ErrorCode.INVALID_INPUT.value,
            message=f"Maximum of {max_files} images allowed per upload.",
            field="images",
            http_status=400,
        )

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    processed: List[ProcessedImage] = []

    for idx, f in enumerate(files):
        # Read file contents
        content = await f.read()

        if len(content) == 0:
            raise AppError(
                code=ErrorCode.INVALID_INPUT.value,
                message=f"Uploaded file '{f.filename}' is empty.",
                field=f"images[{idx}]",
                http_status=400,
            )

        if len(content) > max_bytes:
            raise AppError(
                code=ErrorCode.INVALID_INPUT.value,
                message=f"File '{f.filename}' exceeds maximum allowed size of {settings.MAX_UPLOAD_MB}MB.",
                field=f"images[{idx}]",
                http_status=400,
            )

        # Inspect magic bytes
        mime_type, _ = detect_image_type(content[:16])
        safe_name = sanitize_filename(f.filename or f"image_{idx}")

        processed.append(ProcessedImage(filename=safe_name, mime_type=mime_type, data=content))

    return processed
