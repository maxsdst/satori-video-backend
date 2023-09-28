from pathlib import Path

import ffmpeg
import m3u8
from PIL import Image, UnidentifiedImageError

from videos.video_processing import (
    create_thumbnail,
    create_vertical_video,
    extract_first_frame,
    ffprobe,
    get_video_duration,
    has_audio_stream,
    make_hls,
)


def has_9_16_ratio(width: int, height: int) -> bool:
    return abs(width / height - 9 / 16) < 0.01


def is_valid_video(input: Path) -> bool:
    try:
        probe = ffmpeg.probe(str(input))
    except ffmpeg.Error:
        return False

    return any(stream["codec_type"] == "video" for stream in probe["streams"])


def is_valid_image(input: Path) -> bool:
    try:
        with Image.open(input) as image:
            image.verify()
    except UnidentifiedImageError:
        return False

    return True


def is_valid_hls(playlist_path: Path) -> bool:
    try:
        main_playlist = m3u8.loads(playlist_path.read_text())
    except ValueError:
        return False

    for playlist in main_playlist.playlists:
        path = playlist_path.parent / playlist.uri
        playlist = m3u8.loads(path.read_text())

        for segment in playlist.segments:
            path = playlist_path.parent / segment.uri
            if not is_valid_video(path):
                return False

    return True


class TestCreateVerticalVideo:
    def test_created_video_is_valid(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)
            output_path = temp_dir / "output.mp4"

            create_vertical_video(video_path, output_path)

            assert is_valid_video(output_path)

    def test_if_video_is_horizontal_crops_to_9_16_ratio(
        self, generate_blank_video, temp_dir
    ):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)
            output_path = temp_dir / "output.mp4"

            create_vertical_video(video_path, output_path)
            probe = ffmpeg.probe(str(output_path))
            stream = probe["streams"][0]
            width, height = stream["width"], stream["height"]

            assert height == 240
            assert has_9_16_ratio(width, height)

    def test_if_video_is_vertical_crops_to_9_16_ratio(
        self, generate_blank_video, temp_dir
    ):
        with generate_blank_video(
            width=240, height=320, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)
            output_path = temp_dir / "output.mp4"

            create_vertical_video(video_path, output_path)
            probe = ffmpeg.probe(str(output_path))
            stream = probe["streams"][0]
            width, height = stream["width"], stream["height"]

            assert height == 320
            assert has_9_16_ratio(width, height)

    def test_if_video_is_vertical_and_too_high_crops_to_9_16_ratio(
        self, generate_blank_video, temp_dir
    ):
        with generate_blank_video(
            width=360, height=720, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)
            output_path = temp_dir / "output.mp4"

            create_vertical_video(video_path, output_path)
            probe = ffmpeg.probe(str(output_path))
            stream = probe["streams"][0]
            width, height = stream["width"], stream["height"]

            assert width == 360
            assert has_9_16_ratio(width, height)

    def test_audio_is_preserved(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=360, height=720, duration=1, format="mp4", add_audio=True
        ) as video:
            video_path = Path(video.name)
            output_path = temp_dir / "output.mp4"

            create_vertical_video(video_path, output_path)
            probe = ffmpeg.probe(str(output_path))
            streams = probe["streams"]

            assert any(stream["codec_type"] == "audio" for stream in streams)


class TestHasAudioStream:
    def test_if_video_has_audio_returns_true(self, generate_blank_video):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4", add_audio=True
        ) as video:
            video_path = Path(video.name)

            result = has_audio_stream(video_path)

            assert result == True

    def test_if_video_has_no_audio_returns_false(self, generate_blank_video):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4", add_audio=False
        ) as video:
            video_path = Path(video.name)

            result = has_audio_stream(video_path)

            assert result == False


class TestMakeHls:
    def test_hls_playlist_is_created(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4", add_audio=True
        ) as video:
            video_path = Path(video.name)

            playlist_path = make_hls(video_path, temp_dir)

            assert playlist_path.suffix == ".m3u8"
            assert playlist_path.exists()
            assert (temp_dir / playlist_path.name).exists()

    def test_hls_is_valid(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=3840, height=2160, duration=1, format="mp4", add_audio=True
        ) as video:
            video_path = Path(video.name)

            playlist_path = make_hls(video_path, temp_dir)

            assert is_valid_hls(playlist_path)


class TestCreateThumbnail:
    def test_thumbnail_is_created(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)

            thumbnail_path = create_thumbnail(video_path, temp_dir)

            assert thumbnail_path.suffix == ".jpg"
            assert thumbnail_path.exists()
            assert (temp_dir / thumbnail_path.name).exists()

    def test_thumbnail_is_valid_image(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)

            thumbnail_path = create_thumbnail(video_path, temp_dir)

            assert is_valid_image(thumbnail_path)


class TestExtractFirstFrame:
    def test_first_frame_is_created(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)

            first_frame_path = extract_first_frame(video_path, temp_dir)

            assert first_frame_path.suffix == ".jpg"
            assert first_frame_path.exists()
            assert (temp_dir / first_frame_path.name).exists()

    def test_first_frame_is_valid_image(self, generate_blank_video, temp_dir):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_path = Path(video.name)

            first_frame_path = extract_first_frame(video_path, temp_dir)

            assert is_valid_image(first_frame_path)


class TestGetVideoDuration:
    def test_returns_correct_duration(self, generate_blank_video):
        with generate_blank_video(
            width=320, height=240, duration=3, format="mp4"
        ) as video:
            video_bytes = video.read()

            duration = get_video_duration(video_bytes)

            assert duration == 3


class TestFfprobe:
    def test_bytes_input(self, generate_blank_video):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:
            video_bytes = video.read()

            probe = ffprobe(video_bytes)

            assert isinstance(probe, dict)
            assert "format" in probe and isinstance(probe["format"], dict)

    def test_generator_input(self, generate_blank_video):
        with generate_blank_video(
            width=320, height=240, duration=1, format="mp4"
        ) as video:

            def read():
                while True:
                    chunk = video.read(30)
                    if not chunk:
                        break
                    yield chunk

            probe = ffprobe(read())

            assert isinstance(probe, dict)
            assert "format" in probe and isinstance(probe["format"], dict)
