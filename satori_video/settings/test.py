from .common import *


DEBUG = True

TEST = True

SECRET_KEY = "django-insecure-@__74)jxun%=&&y3m^4&(t%1nkbe$)ts6xk6lo0ue2i6i_2$2_"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "app",
        "HOST": "localhost",
        "PORT": 15432,
        "USER": "postgres",
        "PASSWORD": "FireIsComing!",
    }
}

CELERY_BROKER_URL = "redis://localhost:16379/1"

GORSE_ENTRY_POINT = "http://localhost:18087"
GORSE_API_KEY = ""
