import os
from pathlib import Path

import dj_database_url

from .common import *


DEBUG = False

SECRET_KEY = Path(os.environ["SECRET_KEY_FILE"]).read_text()

ALLOWED_HOSTS = ["." + os.environ["DOMAIN_NAME"]]

CORS_ALLOWED_ORIGINS = [
    "http://" + os.environ["DOMAIN_NAME"],
    "https://" + os.environ["DOMAIN_NAME"],
]

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

DATABASES = {
    "default": dj_database_url.parse(Path(os.environ["DATABASE_URL_FILE"]).read_text())
}

CELERY_BROKER_URL = Path(os.environ["REDIS_URL_FILE"]).read_text()

GORSE_ENTRY_POINT = "http://gorse_server:8087"
GORSE_API_KEY = Path(os.environ["GORSE_API_KEY_FILE"]).read_text()
