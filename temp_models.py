# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Agendamentos(models.Model):
    empresa = models.ForeignKey('Empresas', models.DO_NOTHING)
    devedor = models.ForeignKey('Devedores', models.DO_NOTHING)
    acordo_id = models.IntegerField(blank=True, null=True)
    data_abertura = models.DateTimeField()
    data_retorno = models.DateTimeField()
    assunto = models.TextField()
    operador = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'agendamentos'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CoreAgendamento(models.Model):
    id = models.BigAutoField(primary_key=True)
    acordo_id = models.IntegerField(blank=True, null=True)
    data_abertura = models.DateTimeField()
    data_retorno = models.DateTimeField()
    assunto = models.TextField()
    operador = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    devedor = models.ForeignKey('CoreDevedor', models.DO_NOTHING)
    empresa = models.ForeignKey('CoreEmpresa', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'core_agendamento'


class CoreDevedor(models.Model):
    id = models.BigAutoField(primary_key=True)
    tipo_pessoa = models.CharField(max_length=1)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    nome = models.CharField(max_length=255, blank=True, null=True)
    nome_mae = models.CharField(max_length=255, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    razao_social = models.CharField(max_length=255, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    nome_socio = models.CharField(max_length=255, blank=True, null=True)
    cpf_socio = models.CharField(max_length=14, blank=True, null=True)
    rg_socio = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    telefone1 = models.CharField(max_length=20, blank=True, null=True)
    telefone2 = models.CharField(max_length=20, blank=True, null=True)
    telefone3 = models.CharField(max_length=20, blank=True, null=True)
    telefone4 = models.CharField(max_length=20, blank=True, null=True)
    telefone5 = models.CharField(max_length=20, blank=True, null=True)
    telefone6 = models.CharField(max_length=20, blank=True, null=True)
    telefone7 = models.CharField(max_length=20, blank=True, null=True)
    telefone8 = models.CharField(max_length=20, blank=True, null=True)
    telefone9 = models.CharField(max_length=20, blank=True, null=True)
    telefone10 = models.CharField(max_length=20, blank=True, null=True)
    telefone12 = models.CharField(max_length=20, blank=True, null=True)
    telefone_marcos = models.CharField(max_length=20, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    operadora = models.CharField(max_length=255, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    email1 = models.CharField(max_length=255, blank=True, null=True)
    email2 = models.CharField(max_length=255, blank=True, null=True)
    email3 = models.CharField(max_length=255, blank=True, null=True)
    operador = models.CharField(max_length=255, blank=True, null=True)
    primeira_mensagem_cadastro = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    empresa = models.ForeignKey('CoreEmpresa', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'core_devedor'


class CoreEmpresa(models.Model):
    id = models.BigAutoField(primary_key=True)
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18)
    nome_contato = models.CharField(max_length=255, blank=True, null=True)
    cpf_contato = models.CharField(max_length=14, blank=True, null=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    ie = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_financeiro = models.CharField(max_length=20, blank=True, null=True)
    operador = models.CharField(max_length=255, blank=True, null=True)
    supervisor = models.CharField(max_length=255, blank=True, null=True)
    gerente = models.CharField(max_length=255, blank=True, null=True)
    plano = models.CharField(max_length=100, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    email_financeiro = models.CharField(max_length=255, blank=True, null=True)
    valor_adesao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    usuario = models.CharField(max_length=255, blank=True, null=True)
    senha = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'core_empresa'


class CoreTitulo(models.Model):
    id = models.BigAutoField(primary_key=True)
    idtituloref = models.IntegerField(db_column='idTituloRef', blank=True, null=True)  # Field name made lowercase.
    num_titulo = models.IntegerField()
    tipo_doc_id = models.IntegerField()
    dataemissao = models.DateField(db_column='dataEmissao')  # Field name made lowercase.
    datavencimento = models.DateField(db_column='dataVencimento')  # Field name made lowercase.
    datavencimentoreal = models.DateField(db_column='dataVencimentoReal', blank=True, null=True)  # Field name made lowercase.
    datavencimentoprimeira = models.DateField(db_column='dataVencimentoPrimeira', blank=True, null=True)  # Field name made lowercase.
    data_baixa = models.DateField(blank=True, null=True)
    primeiro_vencimento = models.DateField(blank=True, null=True)
    valor = models.FloatField()
    juros = models.FloatField(blank=True, null=True)
    valorrecebido = models.FloatField(db_column='valorRecebido', blank=True, null=True)  # Field name made lowercase.
    total_parcelamento = models.FloatField(blank=True, null=True)
    total_acordo = models.FloatField(blank=True, null=True)
    parcelar_valor = models.FloatField(blank=True, null=True)
    qtde_parcelas = models.IntegerField(blank=True, null=True)
    nprc = models.IntegerField(db_column='nPrc', blank=True, null=True)  # Field name made lowercase.
    intervalo_dias = models.IntegerField(blank=True, null=True)
    forma_pag_id = models.IntegerField(db_column='forma_pag_Id', blank=True, null=True)  # Field name made lowercase.
    statusbaixa = models.IntegerField(db_column='statusBaixa', blank=True, null=True)  # Field name made lowercase.
    acordocomfirmed = models.IntegerField(db_column='acordoComfirmed')  # Field name made lowercase.
    id_cobranca = models.CharField(max_length=255, blank=True, null=True)
    email_enviado = models.CharField(max_length=4, blank=True, null=True)
    data_envio_whatsapp = models.DateField(blank=True, null=True)
    telefone_enviado = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    devedor = models.ForeignKey(CoreDevedor, models.DO_NOTHING)
    empresa = models.ForeignKey(CoreEmpresa, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'core_titulo'


class Devedores(models.Model):
    empresa = models.ForeignKey('Empresas', models.DO_NOTHING)
    tipo_pessoa = models.CharField(max_length=1, db_comment='F = Física, J = Jurídica')
    cpf = models.CharField(max_length=14, blank=True, null=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    nome = models.CharField(max_length=255, blank=True, null=True)
    nome_mae = models.CharField(max_length=255, blank=True, null=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    razao_social = models.CharField(max_length=255, blank=True, null=True)
    nome_fantasia = models.CharField(max_length=255, blank=True, null=True)
    nome_socio = models.CharField(max_length=255, blank=True, null=True)
    cpf_socio = models.CharField(max_length=14, blank=True, null=True)
    rg_socio = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    telefone1 = models.CharField(max_length=20, blank=True, null=True)
    telefone2 = models.CharField(max_length=20, blank=True, null=True)
    telefone3 = models.CharField(max_length=20, blank=True, null=True)
    telefone4 = models.CharField(max_length=20, blank=True, null=True)
    telefone5 = models.CharField(max_length=20, blank=True, null=True)
    telefone6 = models.CharField(max_length=20, blank=True, null=True)
    telefone7 = models.CharField(max_length=20, blank=True, null=True)
    telefone8 = models.CharField(max_length=20, blank=True, null=True)
    telefone9 = models.CharField(max_length=20, blank=True, null=True)
    telefone10 = models.CharField(max_length=20, blank=True, null=True)
    telefone12 = models.CharField(max_length=20, blank=True, null=True)
    telefone_marcos = models.CharField(max_length=20, blank=True, null=True)
    observacao = models.TextField(blank=True, null=True)
    operadora = models.CharField(max_length=255, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    email1 = models.CharField(max_length=255, blank=True, null=True)
    email2 = models.CharField(max_length=255, blank=True, null=True)
    email3 = models.CharField(max_length=255, blank=True, null=True)
    operador = models.CharField(max_length=255, blank=True, null=True)
    primeira_mensagem_cadastro = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'devedores'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Empresas(models.Model):
    razao_social = models.CharField(max_length=255)
    nome_fantasia = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18)
    nome_contato = models.CharField(max_length=255, blank=True, null=True)
    cpf_contato = models.CharField(max_length=14, blank=True, null=True)
    banco = models.CharField(max_length=100, blank=True, null=True)
    ie = models.CharField(max_length=20, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_financeiro = models.CharField(max_length=20, blank=True, null=True)
    operador = models.CharField(max_length=255, blank=True, null=True)
    supervisor = models.CharField(max_length=255, blank=True, null=True)
    gerente = models.CharField(max_length=255, blank=True, null=True)
    plano = models.CharField(max_length=100, blank=True, null=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    uf = models.CharField(max_length=2, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    email_financeiro = models.CharField(max_length=255, blank=True, null=True)
    valor_adesao = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    usuario = models.CharField(max_length=255, blank=True, null=True)
    senha = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'empresas'


class Titulo(models.Model):
    idtituloref = models.IntegerField(db_column='idTituloRef', blank=True, null=True)  # Field name made lowercase.
    devedor = models.ForeignKey(Devedores, models.DO_NOTHING)
    empresa = models.ForeignKey(Empresas, models.DO_NOTHING)
    num_titulo = models.IntegerField()
    tipo_doc_id = models.IntegerField()
    dataemissao = models.DateField(db_column='dataEmissao')  # Field name made lowercase.
    datavencimento = models.DateField(db_column='dataVencimento')  # Field name made lowercase.
    datavencimentoreal = models.DateField(db_column='dataVencimentoReal', blank=True, null=True)  # Field name made lowercase.
    datavencimentoprimeira = models.DateField(db_column='dataVencimentoPrimeira', blank=True, null=True)  # Field name made lowercase.
    data_baixa = models.DateField(blank=True, null=True)
    primeiro_vencimento = models.DateField(blank=True, null=True)
    valor = models.FloatField()
    juros = models.FloatField(blank=True, null=True)
    valorrecebido = models.FloatField(db_column='valorRecebido', blank=True, null=True)  # Field name made lowercase.
    total_parcelamento = models.FloatField(blank=True, null=True)
    total_acordo = models.FloatField(blank=True, null=True)
    parcelar_valor = models.FloatField(blank=True, null=True)
    qtde_parcelas = models.IntegerField(blank=True, null=True)
    nprc = models.IntegerField(db_column='nPrc', blank=True, null=True)  # Field name made lowercase.
    intervalo_dias = models.IntegerField(blank=True, null=True)
    forma_pag_id = models.IntegerField(db_column='forma_pag_Id', blank=True, null=True)  # Field name made lowercase.
    statusbaixa = models.IntegerField(db_column='statusBaixa', blank=True, null=True)  # Field name made lowercase.
    acordocomfirmed = models.IntegerField(db_column='acordoComfirmed')  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    id_cobranca = models.CharField(max_length=255, blank=True, null=True)
    email_enviado = models.CharField(max_length=4, blank=True, null=True)
    data_envio_whatsapp = models.DateField(blank=True, null=True)
    telefone_enviado = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'titulo'


class Usuarios(models.Model):
    nome = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresas, models.DO_NOTHING)
    usuario = models.CharField(unique=True, max_length=100)
    senha = models.CharField(max_length=255, db_comment='Senha armazenada como hash Bcrypt')
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'
