import logging
from django.utils import timezone

from core.models import UserAccessLog  # seu model atual

logger = logging.getLogger(__name__)

class AccessLogMiddleware:
    # caminhos ignorados
    EXCLUDE_PREFIXES = (
        "/static/", "/media/", "/favicon.ico", "/robots.txt",
        "/admin/js/", "/admin/css/", "/__debug__/",
        "/health", "/metrics",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        path = request.path or ""
        if any(path.startswith(p) for p in self.EXCLUDE_PREFIXES):
            return response

        try:
            UserAccessLog.objects.create(
                user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
                ip_address=self.get_client_ip(request),
                user_agent=(request.META.get("HTTP_USER_AGENT", "")[:512]),
                path=(request.get_full_path() or "")[:512],
                method=(request.method or "")[:8],
                # se seu model tiver esses campos, preenche; se não, pode remover
                module=self.get_module(request)[:64] if hasattr(UserAccessLog, "module") else None,
                status_code=int(getattr(response, "status_code", 0)) if hasattr(UserAccessLog, "status_code") else 0,
                timestamp=timezone.now(),  # se o model usa auto_now_add, este campo será ignorado
            )
        except Exception:
            # não deixar o log derrubar a resposta
            logger.debug("Falha ao gravar access log", exc_info=True)

        return response

    def get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")

    def get_module(self, request):
        # tenta namespace do resolver; senão, primeiro segmento da URL
        rm = getattr(request, "resolver_match", None)
        if rm and rm.namespace:
            return rm.namespace
        return (request.path or "/").strip("/").split("/", 1)[0] or "root"
