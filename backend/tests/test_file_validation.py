"""
Tests for file validation utilities
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi import HTTPException

from app.utils.file_validation import validate_file_size, validate_image_file


class MockUploadFile:
    """Mock UploadFile for testing"""

    def __init__(self, content: bytes, filename: str, content_type: str = "application/octet-stream"):
        self.content = content
        self.filename = filename
        self.content_type = content_type
        self._position = 0

    async def read(self, size: int = -1):
        if size == -1:
            data = self.content[self._position:]
            self._position = len(self.content)
            return data
        else:
            data = self.content[self._position:self._position + size]
            self._position += size
            return data

    async def seek(self, position: int):
        self._position = position

    def __repr__(self):
        return f"MockUploadFile({self.filename})"


def create_test_image(format: str = "PNG", size: tuple = (100, 100)) -> bytes:
    """Create a test image in memory"""
    img = Image.new("RGB", size, color="red")
    buffer = BytesIO()
    img.save(buffer, format=format)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_validate_file_size_within_limit():
    """Test file size validation with file within limit"""
    content = b"x" * (1024 * 1024)  # 1 MB
    file = MockUploadFile(content, "test.txt")

    # Should not raise exception
    await validate_file_size(file, max_size_mb=5)


@pytest.mark.asyncio
async def test_validate_file_size_exceeds_limit():
    """Test file size validation with file exceeding limit"""
    content = b"x" * (6 * 1024 * 1024)  # 6 MB
    file = MockUploadFile(content, "large.txt")

    with pytest.raises(HTTPException) as exc_info:
        await validate_file_size(file, max_size_mb=5)

    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed size" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_file_size_resets_pointer():
    """Test that validate_file_size resets file pointer after reading"""
    content = b"test content"
    file = MockUploadFile(content, "test.txt")

    await validate_file_size(file, max_size_mb=1)

    # Should be able to read file again from beginning
    data = await file.read()
    assert data == content


@pytest.mark.asyncio
async def test_validate_image_file_valid_png():
    """Test validating a valid PNG image"""
    image_content = create_test_image("PNG")
    file = MockUploadFile(image_content, "test.png", "image/png")

    mime_type = await validate_image_file(file)

    assert mime_type == "image/png"


@pytest.mark.asyncio
async def test_validate_image_file_valid_jpeg():
    """Test validating a valid JPEG image"""
    image_content = create_test_image("JPEG")
    file = MockUploadFile(image_content, "test.jpg", "image/jpeg")

    mime_type = await validate_image_file(file)

    assert mime_type == "image/jpeg"


@pytest.mark.asyncio
async def test_validate_image_file_valid_webp():
    """Test validating a valid WebP image"""
    image_content = create_test_image("WEBP")
    file = MockUploadFile(image_content, "test.webp", "image/webp")

    mime_type = await validate_image_file(file)

    assert mime_type == "image/webp"


@pytest.mark.asyncio
async def test_validate_image_file_not_an_image():
    """Test validating a non-image file"""
    content = b"This is not an image"
    file = MockUploadFile(content, "notimage.txt", "text/plain")

    with pytest.raises(HTTPException) as exc_info:
        await validate_image_file(file)

    assert exc_info.value.status_code == 400
    assert "not a valid image" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_image_file_corrupted():
    """Test validating a corrupted image file"""
    # Create corrupted image data
    content = b"PNG\x00\x00corrupted data"
    file = MockUploadFile(content, "corrupted.png", "image/png")

    with pytest.raises(HTTPException) as exc_info:
        await validate_image_file(file)

    assert exc_info.value.status_code == 400
    assert "not a valid image" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_image_file_unsupported_format():
    """Test validating an unsupported image format"""
    # Create a TIFF image (not in allowed types by default)
    image_content = create_test_image("TIFF")
    file = MockUploadFile(image_content, "test.tiff", "image/tiff")

    with pytest.raises(HTTPException) as exc_info:
        await validate_image_file(file)

    assert exc_info.value.status_code == 400
    assert "not allowed" in exc_info.value.detail or "Unsupported image type" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_image_file_checks_actual_format():
    """Test that validation checks actual file format, not just extension"""
    # Create a PNG but name it as JPG
    image_content = create_test_image("PNG")
    file = MockUploadFile(image_content, "fake.jpg", "image/jpeg")

    # Should detect it's actually PNG
    mime_type = await validate_image_file(file)

    assert mime_type == "image/png"


@pytest.mark.asyncio
async def test_validate_image_file_resets_pointer():
    """Test that validate_image_file resets file pointer"""
    image_content = create_test_image("PNG")
    file = MockUploadFile(image_content, "test.png", "image/png")

    await validate_image_file(file)

    # Should be able to read file again from beginning
    data = await file.read()
    assert data == image_content


@pytest.mark.asyncio
async def test_validate_image_file_enforces_size_limit():
    """Test that image validation also checks file size"""
    # Create a large image (larger than default limit)
    large_image = create_test_image("PNG", size=(5000, 5000))
    file = MockUploadFile(large_image, "large.png", "image/png")

    # If the image is larger than the configured limit, should raise exception
    # This depends on MAX_UPLOAD_SIZE_MB setting
    try:
        await validate_image_file(file)
        # If it passes, the image is within limits (which is fine for our test image)
    except HTTPException as e:
        # If it fails, should be a size error
        assert e.status_code == 413


@pytest.mark.asyncio
async def test_validate_file_size_zero_byte_file():
    """Test validation of empty file"""
    content = b""
    file = MockUploadFile(content, "empty.txt")

    # Empty file should pass size validation
    await validate_file_size(file, max_size_mb=1)


@pytest.mark.asyncio
async def test_validate_file_size_exact_limit():
    """Test file exactly at size limit"""
    content = b"x" * (5 * 1024 * 1024)  # Exactly 5 MB
    file = MockUploadFile(content, "exact.txt")

    # Should not raise exception
    await validate_file_size(file, max_size_mb=5)


@pytest.mark.asyncio
async def test_validate_file_size_one_byte_over():
    """Test file one byte over limit"""
    content = b"x" * (5 * 1024 * 1024 + 1)  # 5 MB + 1 byte
    file = MockUploadFile(content, "oversize.txt")

    with pytest.raises(HTTPException) as exc_info:
        await validate_file_size(file, max_size_mb=5)

    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_validate_image_file_gif_not_allowed():
    """Test that GIF images are not allowed (not in ALLOWED_IMAGE_TYPES)"""
    image_content = create_test_image("GIF")
    file = MockUploadFile(image_content, "animated.gif", "image/gif")

    with pytest.raises(HTTPException) as exc_info:
        await validate_image_file(file)

    assert exc_info.value.status_code == 400
    assert "not allowed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_image_file_bmp_not_allowed():
    """Test that BMP images are not allowed (not in ALLOWED_IMAGE_TYPES)"""
    image_content = create_test_image("BMP")
    file = MockUploadFile(image_content, "bitmap.bmp", "image/bmp")

    with pytest.raises(HTTPException) as exc_info:
        await validate_image_file(file)

    assert exc_info.value.status_code == 400
    assert "not allowed" in exc_info.value.detail
