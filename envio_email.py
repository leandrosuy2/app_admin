import mysql.connector
import smtplib
import os
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Configuração do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Intercheck!#jksddfofsmdçls$',
    'database': 'app_sistnortecheck',
    'port': 3306
}

def conectar_bd():
    """Cria uma conexão com o banco de dados."""
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return None

def buscar_config_email():
    """Busca as configurações de e-mail no banco de dados para o tipo de envio 'Quitação Parcela'."""
    conn = conectar_bd()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT email, autenticacao, porta, servidor_smtp, senha
        FROM emails_envio
        WHERE tipo_envio = 'Quitação Parcela'
        LIMIT 1;
        """
        cursor.execute(query)
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar configurações de e-mail: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def buscar_template_email():
    """Busca o template de e-mail para o tipo de envio 'Quitação Parcela'."""
    conn = conectar_bd()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT mensagem
        FROM core_emailtemplate
        WHERE tipo_envio = 'Quitação Parcela'
        LIMIT 1;
        """
        cursor.execute(query)
        template = cursor.fetchone()
        return template['mensagem'] if template else None
    except mysql.connector.Error as err:
        print(f"Erro ao buscar template de e-mail: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def buscar_titulos_para_envio():
    """Busca os títulos do devedor específico para envio de e-mail."""
    conn = conectar_bd()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT titulo.id AS id_titulo, titulo.id_cobranca, devedores.nome AS nome_devedor,
               core_empresa.email, core_empresa.nome_fantasia, core_empresa.nome_contato,
               titulo.valorRecebido, titulo.dataVencimento
        FROM titulo
        JOIN devedores ON titulo.devedor_id = devedores.id
        JOIN core_empresa ON devedores.empresa_id = core_empresa.id
        WHERE titulo.data_baixa = CURRENT_DATE
        AND titulo.statusBaixa = 2 
        AND core_empresa.status_empresa = 1
        AND core_empresa_id.id = 35032;
        """
        cursor.execute(query)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Erro ao buscar títulos: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def substituir_variaveis(template, dados):
    """Substitui as variáveis do template pelos valores reais do título."""
    for chave, valor in dados.items():
        template = template.replace(f"{{{{{chave}}}}}", str(valor))
    return template

def enviar_email(config_email, destinatario, assunto, corpo, anexo_path=None):
    """Envia um e-mail com ou sem anexo, utilizando as configurações dinâmicas do banco de dados."""
    try:
        if not config_email:
            print("Erro: Configuração de e-mail não encontrada no banco de dados.")
            return

        mensagem = MIMEMultipart()
        mensagem['From'] = config_email['email']
        mensagem['To'] = destinatario
        mensagem['Subject'] = assunto
        mensagem.attach(MIMEText(corpo, 'plain'))

        if anexo_path and os.path.exists(anexo_path):
            with open(anexo_path, 'rb') as anexo:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(anexo.read())
                encoders.encode_base64(parte)
                parte.add_header('Content-Disposition', f'attachment; filename={os.path.basename(anexo_path)}')
                mensagem.attach(parte)

        with smtplib.SMTP_SSL(config_email['servidor_smtp'], config_email['porta']) as servidor:
            servidor.login(config_email['email'], config_email['senha'])
            servidor.sendmail(config_email['email'], destinatario, mensagem.as_string())

        print(f"E-mail enviado para {destinatario}")
        time.sleep(5)  # Pequeno delay para evitar bloqueios
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {e}")

def processar_titulos_para_envio():
    """Processa os títulos para envio de e-mails."""
    titulos = buscar_titulos_para_envio()
    if not titulos:
        print("Nenhum título encontrado para envio de e-mail.")
        return

    config_email = buscar_config_email()
    if not config_email:
        print("Erro ao recuperar configurações de e-mail. Envio cancelado.")
        return

    template_email = buscar_template_email()
    if not template_email:
        print("Erro: Template de e-mail não encontrado.")
        return

    for titulo in titulos:
        id_titulo = titulo['id_titulo']
        email_destinatario = titulo['email']

        # Dicionário com os dados para substituição
        dados_template = {
            "titulo.id": id_titulo,
            "devedores.nome": titulo['nome_devedor'],
            "titulo.valorRecebido": f"R$ {titulo['valorRecebido']}",
            "core_empresa.nome_contato": titulo['nome_contato'],
            "core_empresa.nome_fantasia": titulo['nome_fantasia']
        }

        # Substitui os placeholders do template
        corpo_email = substituir_variaveis(template_email, dados_template)

        enviar_email(config_email, email_destinatario, f"Quitação de Parcela - {titulo['nome_devedor']}", corpo_email)

if __name__ == "__main__":
    processar_titulos_para_envio()
