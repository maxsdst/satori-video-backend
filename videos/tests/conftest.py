from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO, Generator

import ffmpeg
import pytest
from django.contrib.auth import get_user_model
from django.db.models import signals

from videos.models import Event, Video
from videos.signals import video_created
from videos.signals.handlers import (
    on_post_delete_user_delete_from_recommender,
    on_post_delete_video_delete_from_recommender,
    on_post_save_event_insert_into_recommender,
    on_post_save_user_insert_into_recommender,
    on_video_created_insert_into_recommender,
)


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


@pytest.fixture(autouse=True)
def disconnect_recommender_signal_receivers(request):
    if "recommender" in request.keywords:
        yield
        return

    user_model = get_user_model()

    receivers = (
        (user_model, signals.post_save, on_post_save_user_insert_into_recommender),
        (user_model, signals.post_delete, on_post_delete_user_delete_from_recommender),
        (None, video_created, on_video_created_insert_into_recommender),
        (Video, signals.post_delete, on_post_delete_video_delete_from_recommender),
        (Event, signals.post_save, on_post_save_event_insert_into_recommender),
    )

    for model, signal, receiver in receivers:
        signal.disconnect(receiver, model)

    yield

    for model, signal, receiver in receivers:
        signal.connect(receiver, model)
