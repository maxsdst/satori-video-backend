from uuid import uuid4

from django.http import HttpRequest


def session_id_middleware(get_response):
    def middleware(request: HttpRequest):
        if "id" not in request.session:
            request.session["id"] = uuid4().hex

        return get_response(request)

    return middleware
