from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO, Generator

import ffmpeg
import pytest


@pytest.fixture
def generate_blank_video(generate_blank_image):
    @contextmanager
    def do_generate_blank_video(
        *, width: int, height: int, duration: int, format: str, add_audio: bool = False
    ) -> Generator[BinaryIO, None, None]:
        image = generate_blank_image(width=width, height=height, format="PNG")

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
            ).run(input=image.read())

            with open(output_path, "rb") as file:
                yield file

    return do_generate_blank_video


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
