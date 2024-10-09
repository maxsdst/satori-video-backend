import os
import re
import ssl
from pathlib import Path

import dj_database_url

from .common import *


DEBUG = False

SECRET_KEY = Path(os.environ["SECRET_KEY_FILE"]).read_text()

ALLOWED_HOSTS = re.split("\s*,\s*", os.environ["ALLOWED_HOSTS"])

CORS_ALLOWED_ORIGINS = [
    "http://" + os.environ["DOMAIN_NAME"],
    "https://" + os.environ["DOMAIN_NAME"],
]

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.environ["S3_ACCESS_KEY"],
            "secret_key": Path(os.environ["S3_SECRET_KEY_FILE"]).read_text(),
            "bucket_name": os.environ["S3_BUCKET_NAME"],
            "endpoint_url": os.environ["S3_ENDPOINT_URL"],
            "region_name": os.environ["S3_REGION_NAME"],
            "custom_domain": os.environ.get("S3_CUSTOM_DOMAIN", None),
            "object_parameters": {
                "CacheControl": "max-age=86400",
            },
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

DATABASES = {
    "default": dj_database_url.parse(Path(os.environ["DATABASE_URL_FILE"]).read_text())
}

CELERY_BROKER_URL = Path(os.environ["REDIS_URL_FILE"]).read_text()
CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}

GORSE_ENTRY_POINT = "http://gorse_server:8087"
GORSE_API_KEY = Path(os.environ["GORSE_API_KEY_FILE"]).read_text()
