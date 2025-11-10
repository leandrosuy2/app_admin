"""
Django settings for app project.

Baseado no projeto original, com suporte a:
- admin.negociarcobrancas.com.br  (painel/admin)
- pix.negociarcobrancas.com.br    (páginas públicas de QR PIX)
"""

from pathlib import Path
import os

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Idiomas ---
LANGUAGES = [
    ("pt-br", "Português"),
]

# --- Segurança ---
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-ql6nn)=f(@3@6^2qhj8l4mm9i%nhp@w19=8uu)pg%o6$7g(fq^",  # mantenha igual ao original se necessário
)
DEBUG = True

# Hosts aceitos
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "admin.negociarcobrancas.com.br",
    "pix.negociarcobrancas.com.br",
    "negociarcobrancas.com.br",
    "www.negociarcobrancas.com.br",
]

# Confiança para cabeçalhos de proxy e cookies seguros
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# (Opcional; já forçado no Nginx. Se habilitar aqui, garanta SECURE_PROXY_SSL_HEADER)
# SECURE_SSL_REDIRECT = True

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "core.apps.CoreConfig",
]

# --- Middleware ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # (mantenha apenas UMA versão do seu access log middleware)
    # "core.access_log_middleware.AccessLogMiddleware",  # se este é o caminho correto
    "core.middleware.access_log_middleware.AccessLogMiddleware",
    # Outras middlewares do projeto:
    "core.middleware.permission_denied.HandlePermissionDeniedMiddleware",
]

# --- Arquivos de mídia ---
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# --- URLs / Templates / WSGI ---
ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "app.wsgi.application"

# --- Banco de dados (MySQL local) ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "app",
        "USER": "advassessoria",
        "PASSWORD": "Parceria@2025!",
        "HOST": "localhost",
        "PORT": "3306",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

# --- Validação de senha ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Internacionalização ---
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# --- Arquivos estáticos ---
# OBS: Você está servindo estáticos diretamente pelo Nginx com:
#   location /static/ { alias /home/app_admin/static/; }
# Então este STATIC_URL/STATIC_ROOT é só para o Django (admin, collectstatic etc.)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Chave primária padrão ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Autenticação / redirects ---
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# --- CSRF (ambos os hosts) ---
CSRF_TRUSTED_ORIGINS = [
    "https://admin.negociarcobrancas.com.br",
    "https://pix.negociarcobrancas.com.br",
    "https://negociarcobrancas.com.br",
    "https://www.negociarcobrancas.com.br",
    # Se ainda acessar admin por HTTP em algum fluxo, mantenha a linha abaixo:
    # "http://admin.negociarcobrancas.com.br",
]

# --- Logging (igual ao original, com console) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.db.backends": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
        "django.security.Authentication": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
        "django.request": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
        "django.contrib.auth": {"level": "DEBUG", "handlers": ["console"], "propagate": False},
    },
}

# --- PIX: base pública e credenciais ---
# Base pública para montar os links do QR (sempre o subdomínio "pix")
PIX_PUBLIC_BASE_URL = "https://pix.negociarcobrancas.com.br"

# Inter (certificados e credenciais mTLS/OAuth)
CERT_PATH = "/etc/ssl/inter/Inter_API_Certificado.crt"
KEY_PATH  = "/etc/ssl/inter/Inter_API_Chave.key"

INTER_API_BASE  = "https://cdpj.partners.bancointer.com.br"
INTER_OAUTH_URL = "https://cdpj.partners.bancointer.com.br/oauth/v2/token"

INTER_CLIENT_ID     = "f37ba2a1-4b0a-4c1a-afd9-df1cfe584552"
INTER_CLIENT_SECRET = "78787d84-705d-4f21-a46e-e4504f6411ac"
INTER_SCOPE         = "cob.read cob.write"

# Chave Pix recebedora
INTER_CHAVE_PIX = "973fd055-f619-4d52-a1eb-626184cc94d6"
INTER_DEBUG = True
