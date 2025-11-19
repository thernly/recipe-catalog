"""
File upload validation utilities.
"""

import imghdr
from fastapi import HTTPException, UploadFile

from app.core.config import settings


async def validate_file_size(file: UploadFile, max_size_mb: int = None) -> None:
    """
    Validate that uploaded file size is within allowed limit.

    Args:
        file: The uploaded file
        max_size_mb: Maximum file size in MB (defaults to settings.MAX_UPLOAD_SIZE_MB)

    Raises:
        HTTPException: If file exceeds size limit
    """
    if max_size_mb is None:
        max_size_mb = settings.MAX_UPLOAD_SIZE_MB

    max_bytes = max_size_mb * 1024 * 1024

    # Read file to check size
    contents = await file.read()
    file_size = len(contents)

    # Reset file pointer for subsequent reads
    await file.seek(0)

    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)",
        )


async def validate_image_file(file: UploadFile) -> str:
    """
    Validate that uploaded file is a valid image with allowed type.

    Args:
        file: The uploaded file

    Returns:
        str: The detected MIME type

    Raises:
        HTTPException: If file is not a valid image or type not allowed
    """
    # First validate file size
    await validate_file_size(file)

    # Read file contents for validation
    contents = await file.read()

    # Reset file pointer for subsequent reads
    await file.seek(0)

    # Detect actual image type from file contents (not just extension)
    image_type = imghdr.what(None, h=contents)

    if image_type is None:
        raise HTTPException(
            status_code=400,
            detail="File is not a valid image",
        )

    # Map imghdr types to MIME types
    mime_type_map = {
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }

    mime_type = mime_type_map.get(image_type)
    if not mime_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {image_type}",
        )

    # Check if MIME type is in allowed list
    if mime_type not in settings.ALLOWED_IMAGE_TYPES:
        allowed = ", ".join(settings.ALLOWED_IMAGE_TYPES)
        raise HTTPException(
            status_code=400,
            detail=f"Image type {mime_type} not allowed. Allowed types: {allowed}",
        )

    return mime_type
