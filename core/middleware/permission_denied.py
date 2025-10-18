from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied

class HandlePermissionDeniedMiddleware:
    """
    Middleware para lidar com erros 403 e redirecionar com uma mensagem amigável.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            messages.error(request, "Você não tem permissão para acessar esta funcionalidade.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
