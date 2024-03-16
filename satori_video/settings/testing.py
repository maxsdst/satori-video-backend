from .defaults import *

DEBUG = True
TEST = True

CELERY_BROKER_URL = "redis://localhost:16379/1"

GORSE_ENTRY_POINT = "http://127.0.0.1:18087"
