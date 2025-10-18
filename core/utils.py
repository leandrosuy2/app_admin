import requests
from bs4 import BeautifulSoup


def consultar_cnpj_via_scraping(cnpj):
    url = f"https://cnpj.biz/{cnpj}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Levanta exceção para erros HTTP

        soup = BeautifulSoup(response.text, 'html.parser')
        dados = {
            "razao_social": soup.find('th', text='Razão Social').find_next('td').text.strip() if soup.find('th', text='Razão Social') else None,
            # Outros campos aqui...
        }
        return dados

    except requests.exceptions.RequestException as e:
        return {"erro": f"Erro ao consultar o CNPJ: {e}"}


def valor_por_extenso(valor):
    # Sua implementação de valor_por_extenso
    unidades = [
        '', 'um', 'dois', 'três', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove'
    ]
    dezenas = [
        '', 'dez', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa'
    ]
    centenas = [
        '', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos'
    ]
    especiais = {
        10: 'dez', 11: 'onze', 12: 'doze', 13: 'treze', 14: 'quatorze',
        15: 'quinze', 16: 'dezesseis', 17: 'dezessete', 18: 'dezoito', 19: 'dezenove'
    }

    def numero_por_extenso(n):
        if n == 0:
            return 'zero'
        elif n < 10:
            return unidades[n]
        elif n < 20:
            return especiais[n]
        elif n < 100:
            dezena, unidade = divmod(n, 10)
            return dezenas[dezena] + (f' e {unidades[unidade]}' if unidade else '')
        elif n < 1000:
            centena, resto = divmod(n, 100)
            if n == 100:
                return 'cem'
            return centenas[centena] + (f' e {numero_por_extenso(resto)}' if resto else '')
        else:
            milhar, resto = divmod(n, 1000)
            milhar_extenso = f'{numero_por_extenso(milhar)} mil' if milhar > 1 else 'mil'
            return milhar_extenso + (f' e {numero_por_extenso(resto)}' if resto else '')

    reais, centavos = divmod(round(valor * 100), 100)
    reais_extenso = f'{numero_por_extenso(reais)} real{"s" if reais > 1 else ""}' if reais else ''
    centavos_extenso = f'{numero_por_extenso(centavos)} centavo{"s" if centavos > 1 else ""}' if centavos else ''

    if reais and centavos:
        return f'{reais_extenso} e {centavos_extenso}'
    return reais_extenso or centavos_extenso

# --- Consulta de óbito -------------------------------------------------------
import os
import re
import logging
import requests
from django.core.cache import cache
from django.utils.timezone import now

def _only_digits(s: str) -> str:
    return re.sub(r'\D', '', s or '')

def consultar_obito(cpf: str) -> dict:
    """
    Consulta status de óbito para um CPF numa API externa.
    Usa variáveis de ambiente:
      OBITO_API_URL  (ex.: https://api.seudominio.com/v1)
      OBITO_API_TOKEN (Bearer ...)
    Retorno padronizado:
      {'checked': bool, 'deceased': bool, 'date': str|None, 'source': str|None, 'raw': dict}
    Cache: 1h por CPF.
    """
    cpf = _only_digits(cpf)
    if len(cpf) != 11:
        return {'checked': False, 'deceased': False, 'status': 'NO_CPF'}

    cache_key = f"obito:{cpf}"
    cached = cache.get(cache_key)
    if cached:
        return {**cached, 'cached': True}

    base_url = (os.getenv('OBITO_API_URL') or '').rstrip('/')
    token = os.getenv('OBITO_API_TOKEN') or ''
    if not base_url or not token:
        data = {'checked': False, 'deceased': False, 'status': 'NO_CREDENTIALS'}
        cache.set(cache_key, data, 600)
        return data

    try:
        # Ajuste o endpoint e params conforme a sua API
        url = f"{base_url}/obito"
        resp = requests.get(
            url,
            params={'cpf': cpf},
            headers={'Authorization': f"Bearer {token}", 'Accept': 'application/json'},
            timeout=12,
        )
        resp.raise_for_status()
        j = {}
        try:
            j = resp.json()
        except Exception:
            j = {}

        deceased = bool(
            j.get('deceased') or j.get('obito') or j.get('falecido') or (j.get('status') == 'DECEASED')
        )
        data = {
            'checked': True,
            'deceased': deceased,
            'date': j.get('date') or j.get('data') or j.get('data_obito'),
            'source': j.get('source') or j.get('fonte'),
            'raw': j,
            'fetched_at': now().isoformat(),
        }
    except Exception as e:
        logging.exception("Erro ao consultar óbito")
        data = {'checked': False, 'deceased': False, 'status': 'ERROR', 'error': str(e)}

    cache.set(cache_key, data, 3600)
    return data

# core/utils.py
import re

def limpar_cnpj(valor: str) -> str:
    """Remove tudo que não for dígito do CNPJ."""
    return re.sub(r'\D', '', valor or '')

# (opcionais, caso queira padronizar)
def apenas_digitos(valor: str) -> str:
    return re.sub(r'\D', '', valor or '')

def limpar_cpf(valor: str) -> str:
    return re.sub(r'\D', '', valor or '')
