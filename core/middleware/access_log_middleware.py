import logging
from django.utils import timezone
from django.apps import apps

logger = logging.getLogger(__name__)

class AccessLogMiddleware:
    """
    Loga todas as requisições (admin, lojista, operador, consultor…),
    incluindo anônimas. Ignora static/media etc. Não quebra a request
    caso o log falhe.
    """
    EXCLUDE_PREFIXES = (
        "/static/", "/media/", "/favicon.ico", "/robots.txt",
        "/admin/js/", "/admin/css/", "/__debug__/",
        "/health", "/metrics",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            path = request.path or ""
            if any(path.startswith(p) for p in self.EXCLUDE_PREFIXES):
                return response

            UserAccessLog = apps.get_model("core", "UserAccessLog")

            # só envia campos que realmente existem no model
            model_fields = {f.name for f in UserAccessLog._meta.fields}

            payload = {
                "user": request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                "ip_address": self._client_ip(request) or "",
                "user_agent": (request.META.get("HTTP_USER_AGENT", "")[:512]),
                "path": (request.get_full_path() or "")[:512],
                "method": (request.method or "")[:8],
            }
            if "timestamp" in model_fields:
                payload["timestamp"] = timezone.now()

            if "module" in model_fields:
                payload["module"] = self._module(request)[:64]
            if "status_code" in model_fields:
                payload["status_code"] = int(getattr(response, "status_code", 0))

            UserAccessLog.objects.create(**payload)

        except Exception:
            logger.debug("Falha ao gravar access log", exc_info=True)

        return response

    def _client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")

    def _module(self, request):
        rm = getattr(request, "resolver_match", None)
        if rm and rm.namespace:
            return rm.namespace
        return (request.path or "/").strip("/").split("/", 1)[0] or "root"
