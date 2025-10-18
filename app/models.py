# core/models.py
from django.db import models

# ----- Se você JÁ tiver essa tabela em outro arquivo, remova esta classe -----
class TabelaRemuneracao(models.Model):
    nome = models.CharField(max_length=120)
    # adicione aqui outros campos que você já usa (se houver)
    def __str__(self):
        return self.nome
# -----------------------------------------------------------------------------


class Empresa(models.Model):
    # Identificação
    nome_fantasia        = models.CharField(max_length=255)
    razao_social         = models.CharField(max_length=255)
    cnpj                 = models.CharField(max_length=18, unique=False)  # aceita com máscara ou só dígitos

    # Contato responsável
    nome_contato         = models.CharField(max_length=255, blank=True)
    cpf_contato          = models.CharField(max_length=14,  blank=True)

    # Telefones / e-mails
    telefone             = models.CharField(max_length=20,  blank=True)
    celular              = models.CharField(max_length=20,  blank=True)
    whatsapp_financeiro  = models.CharField(max_length=20,  blank=True)
    email                = models.EmailField(blank=True)
    email_financeiro     = models.EmailField(blank=True)

    # Endereço
    cep                  = models.CharField(max_length=9,   blank=True)
    endereco             = models.CharField(max_length=255, blank=True)
    numero               = models.CharField(max_length=20,  blank=True)
    bairro               = models.CharField(max_length=120, blank=True)
    cidade               = models.CharField(max_length=120, blank=True)
    uf                   = models.CharField(max_length=2,   blank=True)
    ie                   = models.CharField(max_length=30,  blank=True)

    # Plano e implantação (adesão)
    plano                = models.ForeignKey(TabelaRemuneracao, on_delete=models.PROTECT, related_name='empresas')
    valor_adesao         = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # “Implantação”

    # Dados bancários para depósito
    banco_nome           = models.CharField(max_length=120, blank=True)
    agencia              = models.CharField(max_length=20,  blank=True)
    conta                = models.CharField(max_length=30,  blank=True)
    chave_pix            = models.CharField(max_length=120, blank=True)

    # PIX complementares (opcionais)
    nome_favorecido_pix  = models.CharField(max_length=255, blank=True)
    tipo_pix             = models.CharField(max_length=30,  blank=True)  # cpf/cnpj/email/telefone/chave_aleatoria/agencia_conta

    # Condições de negociação aos devedores
    qtd_parcelas         = models.PositiveSmallIntegerField(default=0)
    desconto_total_avista= models.DecimalField(max_digits=6, decimal_places=2, default=0)   # em %
    desconto_total_aprazo= models.DecimalField(max_digits=6, decimal_places=2, default=0)   # em %

    # Responsáveis (texto simples)
    operador             = models.CharField(max_length=120, blank=True)
    supervisor           = models.CharField(max_length=120, blank=True)
    gerente              = models.CharField(max_length=120, blank=True)

    # Logo
    logo                 = models.ImageField(upload_to='logos_empresas/', blank=True, null=True)

    # Audit
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nome_fantasia', 'razao_social']

    def __str__(self):
        return self.nome_fantasia or self.razao_social
