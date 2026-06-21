import uuid


def generate_request_id():
    return uuid.uuid4().hex[:16]


class RequestContextMiddleware:
    def __init__(self, wsgi_app, flask_app):
        self.wsgi_app = wsgi_app
        self.flask_app = flask_app

    def __call__(self, environ, start_response):
        request_id = generate_request_id()
        environ["X_REQUEST_ID"] = request_id

        def custom_start_response(status, headers, exc_info=None):
            headers.append(("X-Request-ID", request_id))
            return start_response(status, headers, exc_info)

        with self.flask_app.app_context():
            pass

        return self.wsgi_app(environ, custom_start_response)


def get_request_id():
    try:
        from flask import g
        return getattr(g, "request_id", "no-request-id")
    except RuntimeError:
        return "no-request-id"
