import json
import subprocess
from inspect import isgenerator
from pathlib import Path
from typing import Generator

import ffmpeg
import ffmpeg_streaming


def create_vertical_video(input: Path, output: Path) -> None:
    """
    Creates vertical video with 9:16 aspect ratio by cropping it.

    Parameters:
        input (Path): Path to original video
        output (Path): Path to output video
    """

    in_file = ffmpeg.input(str(input))
    streams = []

    if has_audio_stream(input):
        streams.append(in_file.audio)

    video = in_file.video.crop(
        "(iw - min(iw, ih / 16 * 9)) / 2",
        "(ih - min(ih, iw / 9 * 16)) / 2",
        "min(iw, ih / 16 * 9)",
        "min(ih, iw / 9 * 16)",
    )

    streams.append(video)

    output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg.output(*streams, str(output)).run()


def has_audio_stream(input: Path) -> bool:
    """
    Checks if video has audio stream.

    Parameters:
        input (Path): Path to video
    """

    probe = ffmpeg.probe(str(input))

    for stream in probe["streams"]:
        if stream["codec_type"] == "audio":
            return True

    return False


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


def create_thumbnail(input: Path, output_folder: Path) -> Path:
    """
    Creates thumbnail for video and writes it to output_folder.
    Returns path to thumbnail.

    Parameters:
        input (Path): Path to video
        output_folder (Path): Path to output folder
    """

    time = "00:00:00"  # first frame
    width = "405"  # 405px x 720px (9:16 ratio)
    file_name = "thumbnail.jpg"

    output = output_folder / file_name

    (
        ffmpeg.input(str(input), ss=time)
        .filter("scale", width, -1)
        .output(str(output), vframes=1)
        .run()
    )

    return output


def extract_first_frame(input: Path, output_folder: Path) -> Path:
    """
    Extract first frame from video and write it to output_folder.
    Returns path to first frame.

    Parameters:
        input (Path): Path to video
        output_folder (Path): Path to output folder
    """

    time = "00:00:00"  # first frame
    file_name = "frame0.jpg"

    output = output_folder / file_name

    ffmpeg.input(str(input), ss=time).output(str(output), vframes=1).run()

    return output


def get_video_duration(file: bytes | Generator[bytes, None, None]) -> float:
    """
    Get duration of the video in seconds.

    Parameters:
        file (bytes | Generator[bytes, None, None]): Video as bytes or generator yielding chunks of it
    """

    probe = ffprobe(file)
    return float(probe["format"]["duration"])


def ffprobe(file: bytes | Generator[bytes, None, None]) -> dict:
    """
    Run ffprobe on the specified file and return a JSON representation of the output.

    Parameters:
        file (bytes | Generator[bytes, None, None]): Video as bytes or generator yielding chunks of it
    """

    args = ["ffprobe", "-show_format", "-of", "json", r"pipe:"]

    process = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )

    try:
        if isgenerator(file):
            for chunk in file:
                process.stdin.write(chunk)
        else:
            process.stdin.write(file)
    except BrokenPipeError:
        pass

    output, _ = process.communicate(timeout=10)

    if process.returncode != 0:
        raise Exception("ffprobe error")

    return json.loads(output)
