import logging
import time
import uuid

from .logging_context import reset_request_id, set_request_id


logger = logging.getLogger("arqia.request")


class APILoggingMiddleware:
    TRACKED_PREFIXES = (
        "/api/analisar/",
        "/api/documentos/",
        "/api/token/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
        token = set_request_id(request_id)
        start = time.perf_counter()
        payload_size = self._content_length(request)

        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            logger.info(
                (
                    "CORS preflight method=%s path=%s origin=%s "
                    "requested_method=%s requested_headers=%s"
                ),
                request.method,
                request.path,
                request.headers.get("Origin", "-"),
                request.headers.get("Access-Control-Request-Method", "-"),
                request.headers.get("Access-Control-Request-Headers", "-"),
            )

        response = None
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            return response
        finally:
            try:
                if self._should_log_request(request.path):
                    duration_ms = int((time.perf_counter() - start) * 1000)
                    user_id = (
                        request.user.id
                        if getattr(request, "user", None) and request.user.is_authenticated
                        else None
                    )
                    status_code = response.status_code if response else 500
                    logger.info(
                        (
                            "API request method=%s path=%s status=%s duration_ms=%s "
                            "user_id=%s payload_size=%s"
                        ),
                        request.method,
                        request.path,
                        status_code,
                        duration_ms,
                        user_id,
                        payload_size,
                    )
            finally:
                reset_request_id(token)

    def _should_log_request(self, path):
        return any(path.startswith(prefix) for prefix in self.TRACKED_PREFIXES)

    @staticmethod
    def _content_length(request):
        value = request.META.get("CONTENT_LENGTH", "0")
        try:
            return int(value) if value else 0
        except (TypeError, ValueError):
            return 0
