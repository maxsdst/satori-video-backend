from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile

from profiles.utils import convert_image_to_jpg, get_available_random_filename


class TestConvertImageToJpg:
    def test_image_gets_converted_to_jpg(self, generate_blank_image, is_valid_image):
        image = generate_blank_image(width=100, height=100, format="PNG")
        file = InMemoryUploadedFile(
            image, "test", image.name, "image/png", image.getbuffer().nbytes, None
        )
        file_path = Path(file.name)

        new_file = convert_image_to_jpg(file, quality=100)
        new_file_path = Path(new_file.name)

        assert new_file_path.suffix == ".jpg"
        assert new_file.content_type == "image/jpeg"
        assert new_file_path.stem == file_path.stem
        assert new_file.field_name == file.field_name
        assert new_file.size is not None
        assert new_file.charset is None
        assert is_valid_image(new_file)


class TestGetAvailableRandomFilename:
    def test_returns_available_filename(self):
        filename = get_available_random_filename(settings.MEDIA_ROOT, ".txt", 10)

        assert not default_storage.exists(str(settings.MEDIA_ROOT / filename))

    def test_raises_exception_after_too_many_attempts(self):
        with pytest.raises(ValueError):
            for i in range(100):
                filename = get_available_random_filename(settings.MEDIA_ROOT, ".txt", 1)
                default_storage.save(filename, StringIO())
