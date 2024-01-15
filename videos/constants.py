from enum import IntEnum
from pathlib import Path


SECONDS_IN_HOUR = 3600
SECONDS_IN_DAY = SECONDS_IN_HOUR * 24

TEMP_FOLDER = Path("temp")
ALLOWED_VIDEO_EXTENSIONS = ("MP4", "MOV", "MPEG", "3GP", "AVI")
VIEW_COUNT_COOLDOWN_SECONDS = 1 * SECONDS_IN_HOUR


class CommentPopularityWeight(IntEnum):
    LIKE = 1
    REPLY = 2


COMMENT_POPULARITY_TIME_DECAY_RATE = 0.001
