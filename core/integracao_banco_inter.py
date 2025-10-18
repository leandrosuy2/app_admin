# core/integracao_banco_inter.py
# -*- coding: utf-8 -*-
"""
Integração Banco Inter — PIX (cobrança imediata)
Fluxo: OAuth2 Client Credentials (mTLS) -> POST /pix/v2/cob -> GET /pix/v2/loc/{id}/qrcode

Settings mínimos em settings.py:
    CERT_PATH = "/etc/ssl/inter/Inter_API_Certificado.crt"
    KEY_PATH  = "/etc/ssl/inter/Inter_API_Chave.key"

    INTER_CLIENT_ID     = "..."
    INTER_CLIENT_SECRET = "..."
    INTER_SCOPE         = "cob.read cob.write"

    INTER_API_BASE  = "https://cdpj.partners.bancointer.com.br"
    INTER_OAUTH_URL = "https://cdpj.partners.bancointer.com.br/oauth/v2/token"

    # Chave Pix recebedora (EVP, CNPJ, e-mail ou telefone)
    INTER_CHAVE_PIX = "973fd055-f619-4d52-a1eb-626184cc94d6"

    # Logs extras (opcional)
    INTER_DEBUG = True
"""

import base64
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as ReqConnectionError, ReadTimeout, ChunkedEncodingError
from urllib3.util.retry import Retry
from http.client import RemoteDisconnected

from django.conf import settings

log = logging.getLogger(__name__)

UA = "NegociarCobrancas/PIX-Inter"  # mude se quiser

# ========= Exceções =========
class InterAuthError(Exception):
    pass

class InterApiError(Exception):
    pass

# ========= Helpers =========
def _get_setting(*names: str, default: Any = None) -> Any:
    for n in names:
        if hasattr(settings, n):
            return getattr(settings, n)
    return default

def _base_url() -> str:
    return _get_setting("INTER_API_BASE", default="https://cdpj.partners.bancointer.com.br").rstrip("/")

def _token_url() -> str:
    return _get_setting("INTER_OAUTH_URL", default="https://cdpj.partners.bancointer.com.br/oauth/v2/token")

def _cert_pair() -> Tuple[str, str]:
    cert_path = _get_setting("CERT_PATH")
    key_path  = _get_setting("KEY_PATH")
    if not cert_path or not key_path:
        raise InterAuthError("CERT_PATH/KEY_PATH ausentes no settings.")
    return cert_path, key_path

def _client_credentials() -> Tuple[str, str]:
    client_id = _get_setting("INTER_CLIENT_ID", "CLIENT_ID")
    client_secret = _get_setting("INTER_CLIENT_SECRET", "CLIENT_SECRET")
    if not client_id or not client_secret:
        raise InterAuthError("CLIENT_ID/CLIENT_SECRET ausentes (defina INTER_CLIENT_ID/INTER_CLIENT_SECRET).")
    return client_id, client_secret

def _parse_valor(valor: Any) -> float:
    try:
        q = Decimal(str(valor)).quantize(Decimal("0.01"))
        return float(q)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Valor inválido: {valor!r}")

def _raise_api_error(r: requests.Response, prefix: str = "") -> None:
    www = r.headers.get("WWW-Authenticate") or r.headers.get("www-authenticate")
    cid = r.headers.get("x-correlation-id") or r.headers.get("x-b3-traceid") or r.headers.get("trace-id")
    try:
        body = r.json()
    except Exception:
        body = (r.text or "").strip()
    parts = [f"{prefix}HTTP {r.status_code}"]
    if www: parts.append(f"WWW-Authenticate: {www}")
    if cid: parts.append(f"CID: {cid}")
    if body: parts.append(f"Body: {body}")
    msg = " | ".join(parts)
    try:
        req_headers = dict(r.request.headers or {})
        req_headers.pop("Authorization", None)
        if bool(_get_setting("INTER_DEBUG", default=False)):
            log.error("Erro API Inter => %s %s | ReqHeaders=%s | RespHeaders=%s",
                      r.request.method, r.request.url, req_headers, dict(r.headers))
    except Exception:
        pass
    log.error("Erro API Inter: %s", msg)
    raise InterApiError(msg)

# ========= Sessões =========
def _make_session(cert_pair: Tuple[str, str]) -> requests.Session:
    s = requests.Session()
    s.cert = cert_pair
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": UA,
        "Accept": "application/json",
        "Connection": "close",
    })
    return s

def _make_public_session() -> requests.Session:
    """Sessão sem cert e sem Authorization (para loc.location externo)."""
    s = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=5)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": UA,
        "Accept": "*/*",
        "Connection": "close",
    })
    return s

def _request_json(session: requests.Session, method: str, url: str,
                  headers: Optional[Dict[str, str]] = None,
                  json_body: Optional[Dict[str, Any]] = None,
                  timeout: int = 30) -> requests.Response:
    last_exc = None
    for attempt in range(1, 4):
        try:
            r = session.request(
                method.upper(), url,
                headers=headers,
                json=json_body if json_body is not None else None,
                timeout=timeout,
            )
            return r
        except (ReqConnectionError, ReadTimeout, ChunkedEncodingError, RemoteDisconnected) as e:
            last_exc = e
            log.warning("Retry %s/3 em %s %s por erro de transporte: %s", attempt, method.upper(), url, e)
    raise InterApiError(f"Falha de transporte ao chamar {method.upper()} {url}: {last_exc}")

# ========= OAuth2 =========
def obter_token_inter(return_payload: bool = False) -> Union[str, Tuple[str, Dict[str, Any]]]:
    url = _token_url()
    client_id, client_secret = _client_credentials()
    cert_pair = _cert_pair()
    sess = _make_session(cert_pair)

    def _post(data: Dict[str, str]) -> requests.Response:
        h = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": UA,
            "Connection": "close",
        }
        return sess.post(url, data=data, headers=h, auth=(client_id, client_secret), timeout=30)

    data = {"grant_type": "client_credentials"}
    scope = _get_setting("INTER_SCOPE")
    if scope:
        data["scope"] = scope

    resp = _post(data)
    if resp.status_code in (400, 401) and "scope" in (resp.text or "").lower():
        resp = _post({"grant_type": "client_credentials"})

    if resp.status_code != 200:
        _raise_api_error(resp, prefix="Token: ")

    payload = resp.json()
    token = payload.get("access_token")
    if not token:
        raise InterAuthError(f"Resposta de token sem access_token: {payload}")

    if return_payload:
        return token, payload
    return token

# ========= PIX =========
def criar_cobranca_pix_imediata(
    valor: Any,
    chave_pix: Optional[str] = None,
    descricao: str = "Cobrança Pix",
    expiracao_segundos: int = 3600,
    devedor_nome: Optional[str] = None,
    devedor_cnpj: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cria a COB e RETORNA imediatamente o Pix Copia-e-Cola (quando disponível),
    sem tentar baixar o QR. Assim evitamos quedas no host spi-qrcode.
    """
    token, payload = obter_token_inter(return_payload=True)
    base = _base_url()
    cert_pair = _cert_pair()
    sess = _make_session(cert_pair)

    valor_float = _parse_valor(valor)
    chave = (chave_pix or _get_setting("INTER_CHAVE_PIX") or "").strip()
    if not chave:
        raise ValueError("INTER_CHAVE_PIX não configurada e nenhuma 'chave_pix' foi informada.")

    payload_cob: Dict[str, Any] = {
        "calendario": {"expiracao": int(expiracao_segundos)},
        "valor": {"original": f"{valor_float:.2f}"},
        "chave": chave,
        "solicitacaoPagador": descricao[:140],
    }
    if devedor_nome and devedor_cnpj:
        cnpj_limpo = "".join(c for c in str(devedor_cnpj) if c.isdigit())
        if cnpj_limpo:
            payload_cob["devedor"] = {"nome": devedor_nome[:200], "cnpj": cnpj_limpo}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": UA,
        "Connection": "close",
    }

    # 1) Cria a COB
    r = _request_json(sess, "POST", f"{base}/pix/v2/cob", headers=headers, json_body=payload_cob, timeout=30)
    if r.status_code not in (200, 201):
        _raise_api_error(r, prefix="Pix COB: ")
    cob = r.json()

    # 2) Use o copia-e-cola que já vem no payload
    brcode = cob.get("pixCopiaECola") or ""
    if brcode:
        # Devolvemos só isso; a view usa 'brcode' para WhatsApp.
        return {"cob": cob, "brcode": brcode}

    # 3) (Opcional) Se algum dia quiser insistir no QR, faça o fetch aqui.
    #    Mas nunca falhe a emissão por causa do QR – apenas logue e siga com brcode vazio.
    try:
        loc = cob.get("loc") or {}
        loc_id = loc.get("id")
        if loc_id:
            rq = _request_json(sess, "GET", f"{base}/pix/v2/loc/{loc_id}/qrcode",
                               headers={"Authorization": headers["Authorization"], "Accept": "application/json",
                                        "User-Agent": UA, "Connection": "close"},
                               timeout=30)
            if rq.status_code == 200:
                return {"cob": cob, "qrcode": rq.json(), "brcode": brcode}
    except Exception as e:
        log.warning("PIX: falha opcional ao obter QR; usando apenas copia-e-cola. Erro: %s", e)

    # 4) Retorna mesmo sem QR
    return {"cob": cob, "brcode": brcode}

def _qr_via_location_public(loc_url: Optional[str],
                            sess_api: Optional[requests.Session],
                            headers_api: Optional[Dict[str, str]],
                            cob: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback: usa loc.location SEM mTLS/Authorization.
    Tenta parsear JSON {'qrcode','imagemQrcode'}; se vier PNG, embala em base64.
    """
    if not loc_url or not isinstance(loc_url, str) or not loc_url.startswith("http"):
        raise InterApiError("Pix QR (fallback): loc.location inválido: %r" % loc_url)

    # Se o loc_url já termina com /qrcode, mantenha; caso contrário, acrescente.
    parsed = urlparse(loc_url)
    if not parsed.path.endswith("/qrcode"):
        loc_url = loc_url.rstrip("/") + "/qrcode"

    sess_pub = _make_public_session()
    try:
        r = _request_json(sess_pub, "GET", loc_url, headers={"Accept": "*/*"}, timeout=30)
    except InterApiError as e:
        # Último recurso: alguns ambientes aceitam a mesma URL com mTLS+Bearer via API;
        # tentamos com a sessão da API, se fornecida.
        if sess_api and headers_api:
            try:
                r = _request_json(sess_api, "GET", loc_url, headers=headers_api, timeout=30)
            except Exception:
                raise e
        else:
            raise e

    if r.status_code != 200:
        _raise_api_error(r, prefix="Pix QR (public): ")

    # pode ser JSON ou PNG
    ct = r.headers.get("Content-Type", "")
    if "application/json" in ct:
        try:
            qr = r.json()
            return {"cob": cob, "qrcode": qr}
        except Exception:
            raise InterApiError("Pix QR (public): JSON inválido na resposta.")

    # se vier imagem/png (binário), converte para base64 e retorna sem 'qrcode' textual
    content = r.content or b""
    if not content:
        raise InterApiError("Pix QR (public): resposta vazia.")
    img_b64 = base64.b64encode(content).decode("ascii")
    qr = {"qrcode": "", "imagemQrcode": img_b64, "contentType": ct or "image/png"}
    return {"cob": cob, "qrcode": qr}

# --- ADIÇÕES PIX: consulta por txid e QR local ---

def consultar_cob_por_txid(txid: str) -> Dict[str, Any]:
    """
    Consulta a cobrança PIX pelo txid no Inter.
    Retorna o JSON da COB (inclui 'pixCopiaECola' quando disponível).
    """
    if not txid:
        raise InterApiError("txid vazio.")

    token, _ = obter_token_inter(return_payload=True)
    base = _base_url()
    cert_pair = _cert_pair()
    sess = _make_session(cert_pair)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "User-Agent": UA,
        "Connection": "close",
    }
    r = _request_json(sess, "GET", f"{base}/pix/v2/cob/{txid}", headers=headers, timeout=30)
    if r.status_code != 200:
        _raise_api_error(r, prefix="Pix COB Consulta: ")
    try:
        return r.json()
    except Exception:
        raise InterApiError("Pix COB Consulta: resposta não JSON.")


def qrcode_png_base64(data: str, box_size: int = 8, border: int = 2) -> str:
    """
    Gera PNG (base64) do QR a partir do Pix Copia-e-Cola, sem depender do host externo.
    Requer 'qrcode' e 'Pillow': pip install qrcode[pil]
    """
    if not data:
        return ""
    try:
        import io, base64
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as e:
        log.warning("Falha ao gerar QR local: %s", e)
        return ""

# ========= Diagnóstico =========
def diagnostico_ambiente() -> Dict[str, Any]:
    info = {
        "api_base": _base_url(),
        "oauth_url": _token_url(),
        "cert_path": _get_setting("CERT_PATH", default=""),
        "key_path": _get_setting("KEY_PATH", default=""),
        "scope_config": _get_setting("INTER_SCOPE", default=None),
        "debug": bool(_get_setting("INTER_DEBUG", default=False)),
        "ua": UA,
    }
    try:
        token, payload = obter_token_inter(return_payload=True)
        scope_str = str(payload.get("scope") or "")
        scopes = set(scope_str.split())
        info.update({
            "token_ok": True,
            "token_scope": scope_str,
            "has_cob_read": "cob.read" in scopes,
            "has_cob_write": "cob.write" in scopes,
        })
    except Exception as e:
        info["token_ok"] = False
        info["token_err"] = str(e)
    return info
