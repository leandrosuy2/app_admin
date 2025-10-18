# integracao_banco_inter.py
# -*- coding: utf-8 -*-
"""
Integração Banco Inter (PJ) — PIX (cobrança imediata) com OAuth2 Client Credentials e mTLS.

Settings esperados (mínimo):
    CERT_PATH = "/etc/ssl/inter/Inter_API_Certificado.crt"
    KEY_PATH  = "/etc/ssl/inter/Inter_API_Chave.key"
    CLIENT_ID = "seu_client_id"              # ou INTER_CLIENT_ID
    CLIENT_SECRET = "seu_client_secret"      # ou INTER_CLIENT_SECRET

Opcionais:
    INTER_API_BASE  = "https://cdpj.partners.bancointer.com.br"     # produção (default)
    INTER_OAUTH_URL = "https://cdpj.partners.bancointer.com.br/oauth/v2/token"
    INTER_SCOPE     = "cob.read cob.write"                          # Pix cobrança imediata
    INTER_CONTA_CORRENTE = "12345678"                               # se houver +1 conta na integração
    INTER_DEBUG = True                                              # logs extras (sem secretos)
"""

from __future__ import annotations
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

import requests
from django.conf import settings

log = logging.getLogger(__name__)

# =========================
# Exceções específicas
# =========================
class InterAuthError(Exception):
    """Falha na autenticação OAuth/mTLS ou token inválido."""


class InterApiError(Exception):
    """Erro de API do Banco Inter (HTTP != 2xx), com corpo detalhado."""


# =========================
# Helpers
# =========================
def _get_setting(*names: str, default: Any = None) -> Any:
    for n in names:
        if hasattr(settings, n):
            return getattr(settings, n)
    return default


def _parse_valor2(valor: Any) -> float:
    """Normaliza valor em float(2 casas)."""
    try:
        q = Decimal(str(valor)).quantize(Decimal("0.01"))
        return float(q)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Valor inválido: {valor!r}")


def _base_url() -> str:
    return _get_setting("INTER_API_BASE", default="https://cdpj.partners.bancointer.com.br").rstrip("/")


def _token_url() -> str:
    return _get_setting("INTER_OAUTH_URL", default="https://cdpj.partners.bancointer.com.br/oauth/v2/token")


def _cert_pair() -> tuple[str, str]:
    cert_path = _get_setting("CERT_PATH")
    key_path  = _get_setting("KEY_PATH")
    if not cert_path or not key_path:
        raise InterAuthError("CERT_PATH/KEY_PATH ausentes no settings.")
    return cert_path, key_path


def _client_credentials() -> tuple[str, str]:
    client_id = _get_setting("INTER_CLIENT_ID", "CLIENT_ID")
    client_secret = _get_setting("INTER_CLIENT_SECRET", "CLIENT_SECRET")
    if not client_id or not client_secret:
        raise InterAuthError("CLIENT_ID/CLIENT_SECRET ausentes.")
    return client_id, client_secret


def _conta_corrente_header(headers: Dict[str, str]) -> None:
    conta = _get_setting("INTER_CONTA_CORRENTE", "INTER_CONTA")
    if conta:
        headers["x-inter-conta-corrente"] = str(conta).strip()


def _raise_api_error(r: requests.Response, prefix: str = "") -> None:
    try:
        j = r.json()
    except Exception:
        j = r.text
    msg = f"{prefix}HTTP {r.status_code} | Body: {j}"
    log.error("Erro API Inter: %s", msg)
    raise InterApiError(msg)


# =========================
# OAuth2 Client Credentials (mTLS)
# =========================
def obter_token_inter() -> str:
    url = _token_url()
    client_id, client_secret = _client_credentials()
    cert_pair = _cert_pair()

    data = {"grant_type": "client_credentials"}
    scope = _get_setting("INTER_SCOPE")
    if scope:
        data["scope"] = scope

    resp = requests.post(
        url, data=data,
        headers={
            "Accept":"application/json",
            "Content-Type":"application/x-www-form-urlencoded",
            "User-Agent":"NORTECHECK-InterClient/1.0",
        },
        auth=(client_id, client_secret),
        cert=cert_pair, timeout=30
    )

    if resp.status_code != 200:
        _raise_api_error(resp, prefix="Token: ")

    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise InterAuthError(f"Resposta de token sem access_token: {payload}")
    return token


# =========================
# PIX — Cobrança imediata
# =========================
def criar_cobranca_pix_imediata(
    valor: Any,
    chave_pix: str,
    descricao: str = "Cobrança Pix",
    expiracao_segundos: int = 3600,
    info_adicionais: Optional[list] = None
) -> Dict[str, Any]:
    """
    Cria uma cobrança Pix imediata (COB) e retorna também o QR Code (texto e imagem base64).
    Requer escopos: cob.write (criar) e cob.read (consultar QR).
    """
    token = obter_token_inter()
    base = _base_url()
    cert_pair = _cert_pair()
    valor_float = _parse_valor2(valor)

    # 1) Cria a COB
    url_cob = f"{base}/pix/v2/cob"
    payload = {
        "calendario": {"expiracao": int(expiracao_segundos)},
        "valor": {"original": f"{valor_float:.2f}"},
        "chave": chave_pix.strip(),
        "solicitacaoPagador": descricao[:140],
    }
    if info_adicionais:
        payload["infoAdicionais"] = info_adicionais

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "NORTECHECK-InterClient/1.0",
    }
    _conta_corrente_header(headers)

    r = requests.post(url_cob, json=payload, headers=headers, cert=cert_pair, timeout=30)
    if r.status_code not in (200, 201):
        _raise_api_error(r, prefix="Pix COB: ")

    cob = r.json()

    # 2) Busca o QR Code via 'loc'
    loc = (cob.get("loc") or {}).get("id")
    qr = {}
    if loc is not None:
        url_qr = f"{base}/pix/v2/loc/{loc}/qrcode"
        rq = requests.get(url_qr, headers=headers, cert=cert_pair, timeout=30)
        if rq.status_code == 200:
            qr = rq.json()
        else:
            _raise_api_error(rq, prefix="Pix QR: ")

    return {"cob": cob, "qrcode": qr}


# =========================
# (Opcional) Diagnóstico simples
# =========================
def diagnostico_ambiente() -> Dict[str, Any]:
    info = {
        "api_base": _base_url(),
        "oauth_url": _token_url(),
        "cert_path": _get_setting("CERT_PATH", default=""),
        "key_path": _get_setting("KEY_PATH", default=""),
        "scope": _get_setting("INTER_SCOPE", default=None),
    }
    try:
        obter_token_inter()
        info["token_ok"] = True
    except Exception as e:
        info["token_ok"] = False
        info["token_err"] = str(e)
    return info
