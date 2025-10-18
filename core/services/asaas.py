import os
import json
import logging
import re
from datetime import date, timedelta
# core/services/asaas.py
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AsaasError(Exception):
    pass


class AsaasClient:
    def __init__(self):
        # chave definida diretamente em settings.py (sem .env)
        env = getattr(settings, "ASAAS_ENV", "production").lower()
        if env not in ("production", "sandbox"):
            env = "production"

        if env == "production":
            self.base_url = getattr(settings, "ASAAS_BASE_URL", "https://www.asaas.com/api/v3")
            self.api_key = getattr(settings, "ASAAS_API_KEY_PROD", "")
        else:
            self.base_url = getattr(settings, "ASAAS_BASE_URL", "https://sandbox.asaas.com/api/v3")
            self.api_key = getattr(settings, "ASAAS_API_KEY_SANDBOX", "")

        if not self.api_key:
            raise AsaasError("Token ASAAS não configurado para o ambiente atual.")

        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "content-type": "application/json",
            "access_token": self.api_key,
        })

    # -------------------- helpers --------------------
    @staticmethod
    def _digits(s: str) -> str:
        return re.sub(r"\D", "", s or "")

    @staticmethod
    def _trim(s: str, n: int) -> str:
        s = (s or "").strip()
        return s[:n] if n else s

    def _normalize_phone_field(self, phone: str):
        """
        Retorna ('mobilePhone'|'phone', valor) se válido (10 ou 11 dígitos).
        Caso contrário, (None, None) para NÃO enviar.
        """
        d = self._digits(phone)
        if len(d) == 11:
            return "mobilePhone", d
        if len(d) == 10:
            return "phone", d
        return None, None

    # -------------------- HTTP --------------------
    def _handle(self, resp: requests.Response):
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}

        if not resp.ok or "errors" in data:
            raise AsaasError(f"{resp.request.method} {resp.request.path_url} falhou: {data}")

        return data

    def _get(self, path, params=None):
        resp = self.session.get(f"{self.base_url}{path}", params=params or {})
        return self._handle(resp)

    def _post(self, path, payload: dict):
        resp = self.session.post(f"{self.base_url}{path}", data=json.dumps(payload))
        return self._handle(resp)

    def _put(self, path, payload: dict):
        resp = self.session.put(f"{self.base_url}{path}", data=json.dumps(payload))
        return self._handle(resp)

    # -------------------- Customers --------------------
    def ensure_customer(
        self,
        name: str,
        cpf_cnpj: str,
        phone: str = None,
        mobile_phone: str = None,
        email: str = None,
        address: str = None,
        address_number: str = None,
        postal_code: str = None,
        city: str = None,
        state: str = None,
        external_reference: str = None,
    ):
        """Cria/atualiza cliente no ASAAS, saneando telefone/CEP e omitindo campos inválidos."""
        cpf_cnpj_digits = self._digits(cpf_cnpj)
        if not cpf_cnpj_digits:
            raise AsaasError("cpf_cnpj não informado para o cliente.")

        # 1) busca por CPF/CNPJ
        data = self._get("/customers", params={"cpfCnpj": cpf_cnpj_digits, "limit": 1})
        items = data.get("data") or []
        found = items[0] if items else None

        # 2) monta payload saneado
        payload = {
            "name": self._trim(name, 100),
            "cpfCnpj": cpf_cnpj_digits,
        }

        # telefone: usa um válido; se nenhum válido, NÃO envia
        key, val = self._normalize_phone_field(mobile_phone or phone or "")
        if key:
            payload[key] = val
        else:
            logger.debug("ASAAS: telefone inválido/ausente; campo não será enviado.")

        if email:
            payload["email"] = self._trim(email, 100).lower()

        if address:
            payload["address"] = self._trim(address, 100)
        if address_number:
            payload["addressNumber"] = self._trim(str(address_number), 10)

        cep = self._digits(postal_code)
        if len(cep) == 8:
            payload["postalCode"] = cep
        else:
            if postal_code:
                logger.debug("ASAAS: CEP inválido; não enviado.")

        if city:
            payload["city"] = self._trim(city, 60)
        if state:
            payload["state"] = self._trim(state, 2).upper()
        if external_reference:
            payload["externalReference"] = self._trim(external_reference, 50)

        # 3) cria ou atualiza
        if found:
            cid = found["id"]
            data = self._put(f"/customers/{cid}", payload)
            return data
        else:
            data = self._post("/customers", payload)
            return data

    # -------------------- Payments --------------------
    def create_payment(
        self,
        customer_id: str,
        value,
        due_date: str,
        billing_type: str = "BOLETO",  # "PIX" | "BOLETO"
        description: str = None,
    ):
        # --- normaliza value para Decimal(2 casas) e valida > 0 ---
        try:
            val = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            raise AsaasError("Valor inválido para a cobrança (value).")

        if val <= 0:
            raise AsaasError("Valor da cobrança deve ser maior que zero.")

        payload = {
            "customer": customer_id,
            "billingType": billing_type,         # 'BOLETO' ou 'PIX'
            "value": float(val),                 # número com 2 casas
            "dueDate": due_date,                 # 'YYYY-MM-DD'
            "description": description or "Cobrança de comissão Nortecheck",
        }
        if description:
            payload["description"] = (description or "")[:255]

        return self._post("/payments", payload)
