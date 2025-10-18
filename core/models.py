from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


# Modelo para Devedores
class Devedor(models.Model):
    TIPO_PESSOA_CHOICES = [
        ('F', 'Física'),
        ('J', 'Jurídica'),
    ]

    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE)
    tipo_pessoa = models.CharField(max_length=1, choices=TIPO_PESSOA_CHOICES)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    cnpj = models.CharField(max_length=18, null=True, blank=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    nome_mae = models.CharField(max_length=255, null=True, blank=True)
    rg = models.CharField(max_length=20, null=True, blank=True)
    razao_social = models.CharField(max_length=255, null=True, blank=True)
    nome_fantasia = models.CharField(max_length=255, null=True, blank=True)
    nome_socio = models.CharField(max_length=255, null=True, blank=True)
    cpf_socio = models.CharField(max_length=14, null=True, blank=True)
    rg_socio = models.CharField(max_length=50, null=True, blank=True)
    module = models.CharField(max_length=64, blank=True)
    module = models.CharField(max_length=20, default='admin')
    status_code = models.PositiveSmallIntegerField(default=0)
    telefone = models.CharField(max_length=50, null=True, blank=True)
    telefone_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone1 = models.CharField(max_length=50, null=True, blank=True)
    telefone1_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone2 = models.CharField(max_length=50, null=True, blank=True)
    telefone2_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone3 = models.CharField(max_length=50, null=True, blank=True)
    telefone3_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone4 = models.CharField(max_length=50, null=True, blank=True)
    telefone4_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone5 = models.CharField(max_length=50, null=True, blank=True)
    telefone5_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone6 = models.CharField(max_length=50, null=True, blank=True)
    telefone6_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone7 = models.CharField(max_length=50, null=True, blank=True)
    telefone7_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone8 = models.CharField(max_length=50, null=True, blank=True)
    telefone8_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone9 = models.CharField(max_length=50, null=True, blank=True)
    telefone9_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    telefone10 = models.CharField(max_length=50, null=True, blank=True)
    telefone10_valido = models.CharField(max_length=15, choices=[('SIM', 'SIM'), ('NAO', 'NAO'), ('NAO VERIFICADO', 'NAO VERIFICADO')], default='NAO VERIFICADO')
    observacao = models.TextField(null=True, blank=True)
    operadora = models.CharField(max_length=255, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=30, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    email1 = models.CharField(max_length=255, null=True, blank=True)
    email2 = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devedores'  # Define explicitamente o nome da tabela no banco

    def __str__(self):
        return self.nome or self.razao_social or f"Devedor {self.id}"

# Modelo para Agendamentos
class Agendamento(models.Model):
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE)
    devedor = models.ForeignKey(Devedor, on_delete=models.CASCADE)
    acordo_id = models.IntegerField(null=True, blank=True)
    data_abertura = models.DateTimeField()
    data_retorno = models.DateTimeField()
    assunto = models.TextField()
    operador = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Agendamento {self.id} - {self.assunto[:20]}"


# Modelo para Empresas
class Empresa(models.Model):
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18)
    nome_contato = models.CharField(max_length=255, null=True, blank=True)
    cpf_contato = models.CharField(max_length=25, null=True, blank=True)
    banco = models.CharField(max_length=100, null=True, blank=True)
    ie = models.CharField(max_length=20, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    celular = models.CharField(max_length=50, null=True, blank=True)
    whatsapp_financeiro = models.CharField(max_length=20, null=True, blank=True)
    operador = models.CharField(max_length=255, null=True, blank=True)
    supervisor = models.CharField(max_length=255, null=True, blank=True)
    gerente = models.CharField(max_length=255, null=True, blank=True)
    plano = models.ForeignKey('TabelaRemuneracao', on_delete=models.SET_NULL, null=True, blank=True)
    cep = models.CharField(max_length=10, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    numero = models.CharField(max_length=10, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    uf = models.CharField(max_length=30, null=True, blank=True)
    cidade = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    email_financeiro = models.CharField(max_length=255, null=True, blank=True)   
    valor_adesao = models.CharField(max_length=100, null=True, blank=True)
    usuario = models.CharField(max_length=255, null=True, blank=True)
    senha = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    nome_favorecido_pix = models.CharField(max_length=255, blank=True, null=True)
    tipo_pix = models.CharField(max_length=255, blank=True, null=True)    
    status_empresa = models.BooleanField(default=True) 
    class Meta:
        db_table = 'core_empresa'

    def __str__(self):
        return self.razao_social






# Modelo para Títulos
class Titulo(models.Model):
    devedor = models.ForeignKey('Devedor', on_delete=models.CASCADE, verbose_name="Devedor")
    empresa = models.ForeignKey('Empresa', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Empresa")
    idTituloRef = models.IntegerField(null=True, blank=True, verbose_name="ID Referência do Título")
    num_titulo = models.IntegerField(verbose_name="Número do Título")
    tipo_doc = models.ForeignKey('TipoDocTitulo', on_delete=models.CASCADE, verbose_name="Tipo de Documento")
    dataEmissao = models.DateField(verbose_name="Data de Emissão")
    dataVencimento = models.DateField(verbose_name="Data de Vencimento")
    dataVencimentoReal = models.DateField(null=True, blank=True, verbose_name="Data de Vencimento Real")
    dataVencimentoPrimeira = models.DateField(null=True, blank=True, verbose_name="Data de Primeiro Vencimento")
    data_baixa = models.DateField(null=True, blank=True, verbose_name="Data de Baixa")
    primeiro_vencimento = models.DateField(null=True, blank=True, verbose_name="Primeiro Vencimento")
    valor = models.FloatField(verbose_name="Valor")
    juros = models.FloatField(null=True, blank=True, verbose_name="Juros")
    valorRecebido = models.FloatField(null=True, blank=True, verbose_name="Valor Recebido")
    total_parcelamento = models.FloatField(null=True, blank=True, verbose_name="Total do Parcelamento")
    total_acordo = models.FloatField(null=True, blank=True, verbose_name="Total do Acordo")
    parcelar_valor = models.FloatField(null=True, blank=True, verbose_name="Valor Parcelado")
    qtde_parcelas = models.IntegerField(null=True, blank=True, verbose_name="Quantidade de Parcelas")
    nPrc = models.IntegerField(null=True, blank=True, verbose_name="Número de Parcelas")
    dias_atraso = models.IntegerField(null=True, blank=True, verbose_name="Quantidade de Parcelas")
    nPrc = models.IntegerField(null=True, blank=True, verbose_name="Número de Parcelas")
    intervalo_dias = models.IntegerField(null=True, blank=True, verbose_name="Intervalo de Dias")
    forma_pag_Id = models.IntegerField(null=True, blank=True, verbose_name="ID da Forma de Pagamento")
    statusBaixa = models.IntegerField(null=True, blank=True, verbose_name="Status da Baixa")
    statusBaixaGeral = models.IntegerField(null=True, blank=True, verbose_name="Status da Baixa")
    acordoComfirmed = models.BooleanField(default=False, verbose_name="Acordo Confirmado")
    id_cobranca = models.CharField(max_length=255, null=True, blank=True, verbose_name="ID da Cobrança")
    email_enviado = models.CharField(max_length=4, null=True, blank=True, verbose_name="Email Enviado")
    data_envio_whatsapp = models.DateField(null=True, blank=True, verbose_name="Data de Envio no WhatsApp")
    telefone_enviado = models.CharField(max_length=15, null=True, blank=True, verbose_name="Telefone Enviado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    ultima_acao = models.DateField(null=True, blank=True, verbose_name="Última Ação")
    comprovante = models.FileField(upload_to='comprovantes/', null=True, blank=True)
    contrato = models.FileField(upload_to='contratos/', null=True, blank=True)
    operador = models.CharField(max_length=255, null=True, blank=True) 
    @property
    def valor_com_juros(self):
        """Soma segura (valor + juros) com 2 casas, tratando None/float/str."""
        def as_decimal(x):
            if x is None:
                return Decimal('0')
            if isinstance(x, Decimal):
                return x
            try:
                return Decimal(str(x))
            except (InvalidOperation, TypeError):
                return Decimal('0')

        v = as_decimal(getattr(self, 'valor', None))
        j = as_decimal(getattr(self, 'juros', None))
        return (v + j).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    

    class Meta:
        db_table = 'titulo'  # Configura explicitamente o nome da tabela no banco
        verbose_name = "Título"
        verbose_name_plural = "Títulos"

    def __str__(self):
        return f"Título {self.num_titulo} - {self.valor:.2f}"




class Acordo(models.Model):
    empresa = models.ForeignKey('core.Empresa', on_delete=models.CASCADE)
    devedor = models.ForeignKey('core.Devedor', on_delete=models.CASCADE)
    titulo = models.ForeignKey('Titulo', on_delete=models.CASCADE)
    entrada = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    data_entrada = models.DateField(null=True, blank=True)
    qtde_prc = models.IntegerField()  # Quantidade de parcelas
    valor_total_negociacao = models.DecimalField(max_digits=10, decimal_places=2)
    diferenca_dias = models.IntegerField(null=True, blank=True)  # Diferenca em dias para juros
    data_baixa = models.DateField(null=True, blank=True)
    venc_primeira_parcela = models.DateField()
    valor_por_parcela = models.DecimalField(max_digits=10, decimal_places=2)
    contato = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tipo_doc_id = models.IntegerField(null=True, blank=True)  # Adicionado o campo tipo_doc_id
    forma_pag_Id = models.IntegerField(null=True, blank=True, verbose_name="ID da Forma de Pagamento")
    @property
    def nome_devedor(self):
        return self.devedor.nome or self.devedor.razao_social or f"Devedor {self.devedor.id}"
        
        
class Parcelamento(models.Model):
    PENDENTE = 'PENDENTE'
    PAGO = 'PAGO'
    STATUS_CHOICES = [
        (PENDENTE, 'Pendente'),
        (PAGO, 'Pago'),
    ]

    PIX = 'PIX'
    BOLETO = 'BOLETO'
    DINHEIRO = 'DINHEIRO'
    CARTAO_CREDITO = 'CARTAO_CREDITO'
    CARTAO_DEBITO = 'CARTAO_DEBITO'
    CHEQUE = 'CHEQUE'
    PAGAMENTO_LOJA = 'PAGAMENTO_LOJA'
    FORMA_PAGAMENTO_CHOICES = [
        (PIX, 'Pix'),
        (BOLETO, 'Boleto'),
        (DINHEIRO, 'Dinheiro'),
        (CARTAO_CREDITO, 'Cartão de Crédito'),
        (CARTAO_DEBITO, 'Cartão de Débito'),
        (CHEQUE, 'Cheque'),
        (PAGAMENTO_LOJA, 'Pagamento na Loja'),
    ]

    acordo = models.ForeignKey(
        'core.Acordo',
        on_delete=models.CASCADE,
        related_name='parcelas'
    )
    parcela_numero = models.IntegerField()
    data_vencimento = models.DateField()
    data_vencimento_parcela = models.DateField(null=True, blank=True)
    data_baixa = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    comprovante = models.FileField(upload_to='comprovantes/', null=True, blank=True)  # Novo campo para o comprovante
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDENTE
    )
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FORMA_PAGAMENTO_CHOICES,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parcela {self.parcela_numero} - {self.valor} ({self.get_status_display()})"



# Modelo para Tipos de Documentos
class TipoDocTitulo(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tipo_doc_titulo'

    def __str__(self):
        return self.name

class Agendamento(models.Model):
    devedor = models.ForeignKey(Devedor, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    data_abertura = models.DateTimeField(null=True, blank=True)
    data_retorno = models.DateTimeField(null=True, blank=True)
    assunto = models.TextField()
    acordo_id = models.IntegerField(null=True, blank=True, verbose_name="ID do acordo")
    operador = models.CharField(max_length=255, blank=True, null=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[('Pendente', 'Pendente'), ('Finalizado', 'Finalizado')],
        default='Pendente'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class FollowUp(models.Model):
    empresa = models.ForeignKey(Empresa, null=True, blank=True, on_delete=models.SET_NULL)
    devedor = models.ForeignKey(Devedor, on_delete=models.CASCADE)
    texto = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follow_up'  # Nome da tabela
        
class UserAccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    path = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=10, null=True, blank=True)  # GET, POST, etc.
    timestamp = models.DateTimeField(default=now)
    
    class Meta:
        db_table = 'core_user_access_log'  # Especificando o nome da tabela

    def __str__(self):
        return f"Access by {self.user} at {self.timestamp}"



class MensagemWhatsapp(models.Model):
    CATEGORIAS = [
        ('Pendentes', 'Pendentes'),
        ('Negociados', 'Negociados'),
        ('Boletos', 'Boletos'),
        ('Cobrança boleto atrasado', 'Cobrança boleto atrasado'),
        ('Novo cliente', 'Novo cliente'),
    ]

    mensagem = models.TextField()
    categoria = models.CharField(max_length=50, choices=CATEGORIAS)

    

    def __str__(self):
        return f"{self.categoria} - {self.mensagem[:50]}"
        
class TabelaRemuneracao(models.Model):
    nome = models.CharField(max_length=255)

    def __str__(self):
        return self.nome

class TabelaRemuneracaoLista(models.Model):
    tabela_remuneracao = models.ForeignKey(TabelaRemuneracao, related_name='listas', on_delete=models.CASCADE)
    de_dias = models.IntegerField()
    ate_dias = models.IntegerField()
    percentual_remuneracao = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        db_table = 'core_TabelaRemuneracaoLista'  # Força o nome da tabela como está no banco de dados


    def __str__(self):
        return f"{self.tabela_remuneracao.nome} ({self.de_dias}-{self.ate_dias} dias)"        
        


class UsersLojistas(models.Model):
    empresa = models.ForeignKey(
        'Empresa', on_delete=models.SET_NULL, null=True, blank=True
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=255, null=True, blank=True)
    credit = models.IntegerField(default=0)
    email_credit = models.IntegerField(default=0)
    whatsapp_credit = models.CharField(max_length=299, default='0')
    address = models.TextField(null=True, blank=True)
    image = models.CharField(max_length=191, null=True, blank=True)
    password = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
        
        

class EmailEnvio(models.Model):
    AUTENTICACAO_CHOICES = [
        ('SSL', 'SSL'),
        ('TLS', 'TLS'),
    ]

    TIPO_ENVIO_CHOICES = [
        ('Quitação Parcela', 'Quitação Parcela'),
        ('Quitação Contrato', 'Quitação Contrato'),
        ('Nova Empresa', 'Nova Empresa'),
        ('Negociação', 'Negociação'),
        ('Boleto', 'Boleto'),
    ]

    email = models.EmailField(unique=True)
    autenticacao = models.CharField(max_length=3, choices=AUTENTICACAO_CHOICES)
    porta = models.IntegerField()
    servidor_smtp = models.CharField(max_length=255)
    tipo_envio = models.CharField(max_length=50, choices=TIPO_ENVIO_CHOICES)
    provedor = models.CharField(max_length=255)
    senha = models.CharField(max_length=255)

    class Meta:
        db_table = "emails_envio"

    def __str__(self):
        return f"{self.email} ({self.tipo_envio})"
        
        
class EmailTemplate(models.Model):
    TIPO_ENVIO_CHOICES = [
        ('Quitação Parcela', 'Quitação Parcela'),
        ('Quitação Contrato', 'Quitação Contrato'),
        ('Nova Empresa', 'Nova Empresa'),
        ('Negociação', 'Negociação'),
        ('Boleto', 'Boleto'),
    ]

    tipo_envio = models.CharField(max_length=50, choices=TIPO_ENVIO_CHOICES)
    mensagem = models.TextField()

    def __str__(self):
        return f"Template: {self.tipo_envio}"        
        


class Boleto(models.Model):
    empresa_id = models.IntegerField(null=True, blank=True)
    codigo_solicitacao = models.CharField(max_length=255, null=True, blank=True)
    seu_numero = models.CharField(max_length=255, null=True, blank=True)
    situacao = models.CharField(max_length=50, null=True, blank=True)
    data_situacao = models.DateField(null=True, blank=True)
    data_emissao = models.DateField(null=True, blank=True)
    data_vencimento = models.DateField(null=True, blank=True)
    valor_nominal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_total_recebido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    origem_recebimento = models.CharField(max_length=50, null=True, blank=True)
    tipo_cobranca = models.CharField(max_length=50, null=True, blank=True)
    pagador_nome = models.CharField(max_length=255, null=True, blank=True)
    pagador_cpf_cnpj = models.CharField(max_length=20, null=True, blank=True)
    nosso_numero = models.CharField(max_length=255, null=True, blank=True)
    linha_digitavel = models.CharField(max_length=255, null=True, blank=True)
    codigo_barras = models.CharField(max_length=255, null=True, blank=True)
    pix_copia_e_cola = models.TextField(null=True, blank=True)
    txid = models.CharField(max_length=255, null=True, blank=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    cobranca_enviada_whatsapp = models.CharField(max_length=4, null=True, blank=True, default="NAO")

    def __str__(self):
        return f"Boleto {self.id} - Empresa {self.empresa_id}"
        