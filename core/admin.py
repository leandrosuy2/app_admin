from django.contrib import admin
from .models import Cobranca


@admin.register(Cobranca)
class CobrancaAdmin(admin.ModelAdmin):
    list_display = ('id', 'empresa', 'data_cobranca', 'valor_comissao', 'pago', 'tipo_anexo', 'created_at')
    list_filter = ('pago', 'tipo_anexo', 'data_cobranca', 'created_at')
    search_fields = ('empresa__razao_social', 'empresa__cnpj', 'id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informações da Empresa', {
            'fields': ('empresa',)
        }),
        ('Dados da Cobrança', {
            'fields': ('data_cobranca', 'valor_comissao', 'pago', 'tipo_anexo')
        }),
        ('Anexos', {
            'fields': ('documento', 'link')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_editable = ('pago',)  # Permite editar o campo pago diretamente na lista
    date_hierarchy = 'data_cobranca'
    ordering = ('-data_cobranca', '-created_at')
