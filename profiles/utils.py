from io import BytesIO
from pathlib import Path

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.crypto import get_random_string
from PIL import Image


def convert_image_to_jpg(
    file: InMemoryUploadedFile, *, quality: int
) -> InMemoryUploadedFile:
    """Convert image as InMemoryUploadedFile to JPG."""

    image = Image.open(file)
    new_image = image.convert("RGB")
    image_data = BytesIO()
    new_image.save(image_data, format="JPEG", quality=quality)
    image_data.seek(0)

    filename = Path(file.name).stem + ".jpg"
    return InMemoryUploadedFile(
        image_data,
        file.field_name,
        filename,
        "image/jpeg",
        image_data.getbuffer().nbytes,
        None,
    )


def get_available_random_filename(parent_dir: Path, suffix: str, length: int) -> str:
    """
    Get random filename that is free on the default storage.

    Parameters:
        parent_dir (Path): Path to parent directory of the file
        suffix (str): Extension of the file with leading period
        length (int): Length of the random filename
    """

    def generate_filename():
        return get_random_string(length) + suffix

    try_count = 0
    try_limit = 10

    filename = generate_filename()
    while default_storage.exists(str(parent_dir / filename)) and try_count < try_limit:
        filename = generate_filename()
        try_count += 1

    if try_count >= try_limit:
        raise ValueError("Try limit exceeded. Filename length may be too short")

    return filename
