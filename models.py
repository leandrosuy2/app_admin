from django.db import models

class Devedor(models.Model):
    TIPO_PESSOA_CHOICES = [
        ('F', 'Física'),
        ('J', 'Jurídica'),
    ]

    empresa_id = models.IntegerField()
    tipo_pessoa = models.CharField(max_length=1, choices=TIPO_PESSOA_CHOICES)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    cnpj = models.CharField(max_length=18, null=True, blank=True)
    contrato = models.FileField(upload_to='contratos/', null=True, blank=True)

    def tem_contrato(self):
        return bool(self.contrato)
    nome = models.CharField(max_length=255, null=True, blank=True)
    nome_mae = models.CharField(max_length=255, null=True, blank=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    razao_social = models.CharField(max_length=255, null=True, blank=True)
    nome_fantasia = models.CharField(max_length=255, null=True, blank=True)
    nome_socio = models.CharField(max_length=255, null=True, blank=True)
    cpf_socio = models.CharField(max_length=14, null=True, blank=True)
    rg_socio = models.CharField(max_length=20, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    telefone1 = models.CharField(max_length=20, null=True, blank=True)
    telefone2 = models.CharField(max_length=20, null=True, blank=True)
    telefone3 = models.CharField(max_length=20, null=True, blank=True)
    telefone4 = models.CharField(max_length=20, null=True, blank=True)
    telefone5 = models.CharField(max_length=20, null=True, blank=True)
    telefone6 = models.CharField(max_length=20, null=True, blank=True)
    telefone7 = models.CharField(max_length=20, null=True, blank=True)
    telefone8 = models.CharField(max_length=20, null=True, blank=True)
    telefone9 = models.CharField(max_length=20, null=True, blank=True)
    telefone10 = models.CharField(max_length=20, null=True, blank=True)
    telefone12 = models.CharField(max_length=20, null=True, blank=True)
    telefone_marcos = models.CharField(max_length=20, null=True, blank=True)
    observacao = models.TextField(null=True, blank=True)
    operadora = models.CharField(max_length=255, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=2, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    email1 = models.CharField(max_length=255, null=True, blank=True)
    email2 = models.CharField(max_length=255, null=True, blank=True)
    email3 = models.CharField(max_length=255, null=True, blank=True)
    operador = models.CharField(max_length=255, null=True, blank=True)
    primeira_mensagem_cadastro = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome or self.razao_social or f"Devedor {self.id}"
