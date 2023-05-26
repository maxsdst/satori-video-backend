from pathlib import Path

import ffmpeg_streaming
from django.conf import settings
from django.core.files.storage import default_storage


def make_hls(input: Path, output_folder: Path) -> Path:
    """
    Packages video for HLS streaming.
    HLS playlist and all related files are written to output_folder.
    Returns path to HLS playlist.

    Parameters:
        input (Path): Path to video
        output_folder (Path): Path to output folder
    """

    output = output_folder / "HLSPlaylist.m3u8"

    video = ffmpeg_streaming.input(str(input))
    hls = video.hls(ffmpeg_streaming.Formats.h264())
    hls.auto_generate_representations()
    hls.output(str(output))

    return output


def get_media_url(target: Path) -> str:
    """Returns URL of the file in MEDIA_ROOT folder."""

    relative_path = str(target).replace(str(settings.MEDIA_ROOT), "")
    return default_storage.url(relative_path)
