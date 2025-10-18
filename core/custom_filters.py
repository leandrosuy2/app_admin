from django import template
import re

register = template.Library()  # Certifique-se de definir 'register'

@register.filter
def clean_phone(value):
    """Remove caracteres não numéricos de um número de telefone e adiciona o código do país."""
    if not value:
        return ''
    clean_value = re.sub(r'\D', '', value)  # Remove tudo que não for número
    return f"55{clean_value}"  # Adiciona o código do país
