import shutil
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO, Generator

import ffmpeg
import pytest
from PIL import Image


@pytest.fixture
def generate_blank_video():
    @contextmanager
    def do_generate_blank_video(
        *, width: int, height: int, duration: int, format: str, add_audio: bool = False
    ) -> Generator[BinaryIO, None, None]:
        image = Image.new("RGB", (width, height), color="red")
        image_data = BytesIO()
        image.save(image_data, format="PNG")
        image_data.seek(0)

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / ("output." + format)

            streams = []

            video = ffmpeg.input("pipe:", loop=1)
            streams.append(video)

            if add_audio:
                audio = ffmpeg.input("anullsrc", f="lavfi")
                streams.append(audio)

            ffmpeg.output(
                *streams,
                str(output_path),
                t=duration,
                pix_fmt="yuv420p",
                r=1,
            ).run(input=image_data.read())

            with open(output_path, "rb") as file:
                yield file

    return do_generate_blank_video


@pytest.fixture(autouse=True)
def media_root(settings):
    settings.MEDIA_ROOT = settings.BASE_DIR / "media_test"
    shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
    settings.MEDIA_ROOT.mkdir()
    yield
    shutil.rmtree(settings.MEDIA_ROOT)


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
