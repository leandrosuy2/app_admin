# core/templatetags/custom_filters.py
from django import template
from decimal import Decimal
import re
import datetime

# usa a sua função existente
from core.utils import valor_por_extenso as _valor_por_extenso

register = template.Library()

@register.filter
def get_value(dictionary, key):
    """Retorna o valor de um dicionário para uma chave específica."""
    try:
        return dictionary.get(key, "")
    except Exception:
        return ""

@register.filter
def replace(value, args):
    """
    Substitui partes de uma string.
    Uso: {{ value|replace:"old,new" }}
    """
    try:
        old, new = args.split(",", 1)
        return str(value).replace(old, new)
    except Exception:
        return value

@register.filter
def coalesce(value1, value2):
    """Retorna o primeiro valor não nulo/não vazio."""
    return value1 or value2

@register.filter
def clean_phone_number(value):
    """Remove caracteres não numéricos de um número de telefone."""
    if not value:
        return ""
    return re.sub(r"[^0-9]", "", str(value))

@register.filter
def traduz_permissao(name):
    n = (name or "").lower()
    if n.startswith("can add"):
        return "Pode adicionar"
    if n.startswith("can change"):
        return "Pode editar"
    if n.startswith("can delete"):
        return "Pode excluir"
    if n.startswith("can view"):
        return "Pode visualizar"
    return name

@register.filter
def data_por_extenso(value):
    """Converte datetime.date em 'd de mês de yyyy'."""
    if isinstance(value, datetime.date):
        meses = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        return f"{value.day} de {meses[value.month - 1]} de {value.year}"
    return value

@register.filter(name="valor_por_extenso")
def valor_por_extenso_filter(valor):
    """Wrapper para core.utils.valor_por_extenso."""
    try:
        return _valor_por_extenso(valor)
    except Exception:
        return ""

@register.filter
def get_dict_value(dictionary, key):
    """Retorna o valor de um dicionário para uma chave específica."""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "Não informado")
    return "Não informado"

@register.filter
def mul(value, arg):
    """Multiplica dois valores numéricos (suporta Decimal)."""
    try:
        v = Decimal(str(value))
        a = Decimal(str(arg))
        return v * a
    except Exception:
        try:
            return float(value) * float(arg)
        except Exception:
            return 0

@register.filter
def get_item(d, key):
    """
    Acessa d[key] em templates Django: {{ dict|get_item:chave }}
    Retorna None se não existir.
    """
    try:
        return d.get(key)
    except Exception:
        return None
