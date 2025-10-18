# core/integracao_cora.py
import os, requests
from django.conf import settings

class CoraConfigError(RuntimeError): pass

def _get_conf(attr, env):
    v = getattr(settings, attr, None) or os.getenv(env) or ""
    v = v.strip() if isinstance(v, str) else ""
    if not v:
        raise CoraConfigError(f"Config ausente: {attr} (ou variável {env})")
    return v

def _tok():
    url = _get_conf("CORA_OAUTH_URL", "CORA_OAUTH_URL")
    cid = _get_conf("CORA_CLIENT_ID", "CORA_CLIENT_ID")
    csc = _get_conf("CORA_CLIENT_SECRET", "CORA_CLIENT_SECRET")
    scope = getattr(settings, "CORA_SCOPE", os.getenv("CORA_SCOPE", "charges.read charges.write"))
    r = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": cid,
        "client_secret": csc,
        "scope": scope,
    }, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]

def cora_criar_boleto(valor, pagador_nome, pagador_documento, vencimento, mensagem):
    base = _get_conf("CORA_API_BASE", "CORA_API_BASE")
    url  = f"{base.rstrip('/')}/charges"
    tok  = _tok()

    payload = {
        "type": "BOLETO",
        "amount": float(valor),
        "description": mensagem,
        "dueDate": vencimento,  # YYYY-MM-DD
        "customer": {"name": pagador_nome, "document": pagador_documento},
        # "pix": {"enabled": True},  # habilite se sua conta exigir para boleto vir com Pix
    }

    r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    r.raise_for_status()
    data = r.json()

    pix = data.get("pix") or {}
    brcode = (
        pix.get("copyAndPaste") or pix.get("copiaECola") or
        data.get("pixCopiaECola") or data.get("brcode") or ""
    )
    txid = pix.get("txid") or data.get("txid")

    return {
        "id":             data.get("id") or data.get("chargeId"),
        "digitable_line": data.get("digitableLine") or data.get("linhaDigitavel"),
        "barcode":        data.get("barCode") or data.get("barcode") or data.get("codigoBarras"),
        "boleto_url":     data.get("link") or data.get("boletoUrl") or data.get("url"),
        "pdf_url":        data.get("pdfUrl") or data.get("pdf"),
        "nosso_numero":   data.get("nossoNumero"),
        "pix_brcode":     brcode or "",
        "pix_txid":       txid or "",
    }
