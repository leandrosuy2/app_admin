# core/templatetags/bool_filters.py
from django import template

register = template.Library()

@register.filter
def as_bool(value):
    """
    Converte '0'/'1', 0/1, 'true'/'false' etc. em booleano.
    """
    if isinstance(value, bool):
        return value
    try:
        return int(value) != 0
    except Exception:
        s = str(value).strip().lower()
        return s in ("1", "true", "t", "yes", "y", "on")
