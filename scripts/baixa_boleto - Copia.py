import mysql.connector
import requests
import base64
from datetime import datetime, timedelta
import time  
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Configuração do banco de dados
db_config = {
    'host': 'xsender_db.mysql.dbaas.com.br',
    'user': 'xsender_db',
    'password': 'Parceria@2020',
    'database': 'xsender_db',
    'port': 3306
}

# Configuração da API do Banco Inter
api_config = {
    'cert_path': '/home/advassessoria/core/certificados/Inter_API_Certificado.crt',
    'key_path': '/home/advassessoria/core/certificados/Inter_API_Chave.key',
    'token_url': 'https://cdpj.partners.bancointer.com.br/oauth/v2/token',
    'boleto_pdf_url': 'https://cdpj.partners.bancointer.com.br/cobranca/v3/cobrancas/{id_cobranca}/pdf',
    'client_id': 'd20fd198-76f1-4301-9494-56e92738fa89',
    'client_secret': '7c7a9406-f73b-4af2-8a61-d7b68493ec68',
    'conta_corrente': '295101610'  # Substitua pelo número correto da conta
}

# Configurações do servidor SMTP da Locaweb
smtp_config = {
    'host': 'email-ssl.com.br',
    'port': 465,  # Porta SSL
    'user': 'financeiroadv@advassessoria.com.br',
    'password': '@MA290996ju'  # Substitua pela senha correta
}




def calcular_valor_boleto(valor_recebido, data_vencimento):
    """
    Calcula o valor do boleto com base no valor recebido, a data de vencimento e a tabela de taxas.
    :param valor_recebido: O valor original do título.
    :param data_vencimento: A data de vencimento do boleto no formato 'dd/mm/yyyy'.
    :return: O valor do boleto com a taxa aplicada.
    """
    # Ajuste: Converter a data de vencimento para o formato correto
    try:
        data_vencimento_obj = datetime.strptime(data_vencimento, "%d/%m/%Y")  # Converter dataVencimento para datetime
    except ValueError:
        print(f"Erro: O formato da data {data_vencimento} não é válido. Use o formato dd/mm/yyyy.")
        raise

    # Calcular a diferença de dias entre a data de vencimento e a data atual
    dias_atraso = (datetime.now() - data_vencimento_obj).days  # Calcular o número de dias de atraso

    # Definir a taxa com base no número de dias de atraso
    if 30 <= dias_atraso <= 45:
        taxa = 0.06  # 06% para atraso entre 30 e 45 dias
    elif 46 <= dias_atraso <= 90:
        taxa = 0.09  # 09% para atraso entre 46 e 90 dias
    elif 91 <= dias_atraso <= 120:
        taxa = 0.12  # 12% para atraso entre 91 e 120 dias
    elif 121 <= dias_atraso <= 180:
        taxa = 0.15  # 15% para atraso entre 121 e 180 dias
    elif 181 <= dias_atraso <= 360:
        taxa = 0.18  # 18% para atraso entre 181 e 360 dias
    elif 361 <= dias_atraso <= 720:
        taxa = 0.23  # 23% para atraso entre 361 e 720 dias
    elif 721 <= dias_atraso <= 1095:
        taxa = 0.26  # 26% para atraso entre 721 e 1095 dias
    elif dias_atraso > 1095:
        taxa = 0.30  # 30% para atraso acima de 1095 dias
    else:
        taxa = 0  # Se não houver atraso, taxa 0%

    # Calcular o percentual aplicado no valor recebido
    percentual_boleto = valor_recebido * taxa  # Calcula o valor do percentual do atraso sobre o valor recebido
    valor_boleto = round(percentual_boleto, 2)  # Arredonda para duas casas decimais

    return valor_boleto, dias_atraso, round(taxa * 100, 2)  # Retorna o valor do boleto (percentual aplicado), dias de atraso e o percentual aplicado
def obter_token():
    """
    Obtém o token de acesso do Banco Inter.
    """
    request_body = (
        f"client_id={api_config['client_id']}&"
        f"client_secret={api_config['client_secret']}&"
        "scope=boleto-cobranca.read&"
        "grant_type=client_credentials"
    )

    try:
        response = requests.post(
            api_config['token_url'],
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            cert=(api_config['cert_path'], api_config['key_path']),
            data=request_body
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        print(f"Token obtido com sucesso: {token}")
        return token
    except requests.RequestException as e:
        print("Erro ao obter token:", e)
        print("Resposta do servidor:", e.response.text if e.response else "Sem resposta")
        raise

def buscar_id_cobranca():
    """
    Conecta ao banco de dados e busca o id_cobranca onde titulo_devedor.id = 4430.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = "SELECT id_cobranca FROM titulo_devedor WHERE id = %s"
        cursor.execute(query, (6083,))
        result = cursor.fetchone()

        if result:
            id_cobranca = result[0]
            print(f"ID Cobrança encontrado: {id_cobranca}")
            return id_cobranca
        else:
            print("Nenhum ID de cobrança encontrado para o título com ID 4430.")
            return None
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def baixar_boleto(id_cobranca):
    """
    Faz o download do PDF do boleto com base no ID da cobrança.
    Retorna o caminho do arquivo salvo.
    """
    token = obter_token()
    url = api_config['boleto_pdf_url'].format(id_cobranca=id_cobranca)
    headers = {
        "Authorization": f"Bearer {token}",
        "x-conta-corrente": api_config['conta_corrente']
    }

    print(f"Iniciando download do boleto de URL: {url}")
    print(f"Enviando cabeçalhos: {headers}")

    try:
        response = requests.get(
            url,
            headers=headers,
            cert=(api_config['cert_path'], api_config['key_path'])
        )
        response.raise_for_status()

        if response.headers.get("Content-Type") == "application/json":
            data = response.json()
            if "pdf" in data:
                pdf_content = base64.b64decode(data["pdf"])
                pdf_filename = f"/home/advassessoria/core/boletos/boleto_{id_cobranca}.pdf"

                with open(pdf_filename, "wb") as file:
                    file.write(pdf_content)
                print(f"Boleto salvo com sucesso como: {pdf_filename}")
                return pdf_filename  # Retorna o nome do arquivo
            else:
                raise Exception("PDF não encontrado na resposta JSON.")
        else:
            pdf_filename = f"boleto_{id_cobranca}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            with open(pdf_filename, "wb") as file:
                file.write(response.content)
            print(f"Boleto salvo com sucesso como: {pdf_filename}")
            return pdf_filename  # Retorna o nome do arquivo
    except requests.RequestException as e:
        print("Erro ao baixar o boleto:", e)
        raise

def buscar_dados_destinatario(id_titulo_devedor):
    """
    Busca os dados necessários para o corpo do e-mail com base no ID do título devedor.
    Retorna as variáveis como: valorRecebido, nome do devedor, e-mail do destinatário, nome do contato, e data de vencimento.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Consulta para obter os dados necessários para o corpo do e-mail
        query = """
        SELECT titulo_devedor.valorRecebido, 
               devedores.nome AS nome_devedor, 
               companies.email, 
               companies.id, 
               companies.nome_contato,
               titulo_devedor.dataVencimento
        FROM titulo_devedor
        JOIN devedores ON titulo_devedor.devedorId = devedores.id
        JOIN companies ON companies.id = devedores.company_id
        WHERE titulo_devedor.id = %s
        """
        cursor.execute(query, (id_titulo_devedor,))
        result = cursor.fetchone()

        if result:
            valor_recebido = result[0]
            nome_devedor = result[1]
            email_destinatario = result[2]
            nome_contato = result[4]
            data_vencimento = result[5].strftime("%d/%m/%Y")  # Convertendo para formato dd/mm/yyyy

            print(f"Dados encontrados: {nome_devedor}, {email_destinatario}, {data_vencimento}")
            return valor_recebido, nome_devedor, email_destinatario, nome_contato, data_vencimento
        else:
            print(f"Nenhum dado encontrado para o título devedor ID {id_titulo_devedor}.")
            return None
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def buscar_email_destinatario(id_titulo_devedor):
    """
    Busca o e-mail do destinatário com base no ID do título devedor, 
    utilizando a consulta corrigida com as tabelas 'titulo_devedor', 'devedores' e 'companies'.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Consulta para obter o e-mail correto usando a junção das tabelas
        query = """
        SELECT companies.email
        FROM titulo_devedor
        JOIN devedores ON titulo_devedor.devedorId = devedores.id
        JOIN companies ON companies.id = devedores.company_id
        WHERE titulo_devedor.id = %s
        """
        cursor.execute(query, (id_titulo_devedor,))
        result = cursor.fetchone()

        if result:
            email_destinatario = result[0]
            print(f"E-mail do destinatário encontrado: {email_destinatario}")
            return email_destinatario
        else:
            print(f"Nenhum e-mail encontrado para o título devedor ID {id_titulo_devedor}.")
            return None
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



def enviar_email_boleto(destinatario, assunto, corpo, anexo_path=None, bcc=None, nome_contato=None, nome_devedor=None, data_vencimento=None, valor_recebido=None, valor_boleto=None, percentual_boleto=None):
    """
    Envia um e-mail com ou sem anexo utilizando o servidor SMTP configurado.
    :param destinatario: E-mail do destinatário principal.
    :param assunto: Assunto do e-mail.
    :param corpo: Corpo do e-mail (texto plano).
    :param anexo_path: Caminho do arquivo para anexar (opcional).
    :param bcc: E-mail para cópia oculta (opcional).
    :param nome_contato: Nome do contato da empresa (de 'companies.nome_contato')
    :param nome_devedor: Nome do devedor (de 'devedores.nome')
    :param data_vencimento: Data de vencimento (de 'titulo_devedor.dataVencimento')
    :param valor_recebido: Valor recebido (de 'titulo_devedor.valorRecebido')
    :param valor_boleto: Valor do boleto gerado
    :param percentual_boleto: Percentual do boleto em relação ao valor recebido
    """
    # Formatação do corpo do e-mail com as variáveis
    corpo_email = f"""
Atte.

SRº (ª) {nome_contato}

Segue boleto do pagamento dos serviços prestados de cobrança.

Comunicamos de acordo com contrato, que a empresa Adv. Assessoria foi contratada para prestação de serviços de Cobranças, do credor empresa. Dessa maneira, informamos que o pagamento da prestação de serviços de Cobranças poderá ser feito por meio de Depósito e boleto, que segue em anexo, à vista.

Protesto automático pela rede bancária após 5 dias de vencimento.

Referente: {nome_devedor}

Valor recebido: {valor_recebido}
Vencimento do titulo: {data_vencimento} 
Honorário e Percentual do valor do boleto: {int(percentual_boleto)}% de R$ {valor_recebido}

VALOR TOTAL: R$ {valor_boleto}

Atenção: o não pagamento do valor abaixo descrito, por parte do credor, será reativado automaticamente pelo sistema com prazo de 5 dias. O(s) devedor(es) será(ão) cobrado(s) sucessivamente até a efetiva baixa do débito. Junto à Adv. Assessoria.

Art. 43, § 2º do Código de Defesa do Consumidor - Lei 8078/90

CDC - Lei nº 8.078 de 11 de Setembro de 1990

Dispõe sobre a proteção do consumidor e dá outras providências.

Art. 43. O consumidor, sem prejuízo do disposto no art. 86, terá acesso às informações existentes em cadastros, fichas, registros e dados pessoais e de consumo arquivados sobre ele, bem como sobre as suas respectivas fontes.

Do Código de Defesa do Consumidor. Nesse sentido, é sabido que o artigo 2º da Lei nº 8.078/90 conceitua consumidor como "toda pessoa física ou jurídica". Em indenização por dano moral. Observância da formalidade prevista no artigo 43.

Atenciosamente,

Adv Assessoria

Telefone: (WhatsApp) +55(11)91174-1586

E-mail: financeiroadv@advassessoria.com.br

http://www.advassessoria.com.br
"""
    try:
        # Criação da mensagem
        mensagem = MIMEMultipart()
        mensagem['From'] = smtp_config['user']
        mensagem['To'] = destinatario  # Envia para o destinatário principal
        mensagem['Subject'] = "Boleto do Pagamento dos Serviços Prestado de Cobrança" 
        if bcc:
            mensagem['Bcc'] = bcc  # Adiciona o endereço de CCO (cópia oculta)
        mensagem.attach(MIMEText(corpo_email, 'plain'))

        # Adiciona o anexo, se fornecido
        if anexo_path and os.path.exists(anexo_path):
            with open(anexo_path, 'rb') as anexo:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(anexo.read())
                encoders.encode_base64(parte)
                parte.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(anexo_path)}'
                )
                mensagem.attach(parte)

        # Conexão com o servidor SMTP
        with smtplib.SMTP_SSL(smtp_config['host'], smtp_config['port']) as servidor:
            servidor.login(smtp_config['user'], smtp_config['password'])
            servidor.sendmail(
                smtp_config['user'],
                [destinatario] + ([bcc] if bcc else []),  # Envia para o destinatário e CCO
                mensagem.as_string()
            )
        print('E-mail enviado com sucesso!')

        # Atraso de 10 segundos antes de enviar o próximo e-mail (aumentado para evitar bloqueios)
        time.sleep(10)  # Ajuste esse valor conforme necessário

    except Exception as e:
        print(f'Falha ao enviar o e-mail: {e}')


def main():
    try:
        id_titulo_devedor = 4430  # ID do título devedor que você está processando
        id_cobranca = buscar_id_cobranca()  # Função que retorna o ID da cobrança

        if id_cobranca:
            # Buscar os dados necessários para o corpo do e-mail
            dados = buscar_dados_destinatario(id_titulo_devedor)
            if not dados:
                print("Não foi possível encontrar os dados do destinatário.")
                return

            valor_recebido, nome_devedor, email_destinatario, nome_contato, data_vencimento = dados

            # Calcular o valor do boleto com base na data de vencimento e valor recebido
            valor_boleto, dias_atraso, percentual_boleto = calcular_valor_boleto(valor_recebido, data_vencimento)

            # Baixar o boleto
            pdf_filename = baixar_boleto(id_cobranca)

            # Configurar e enviar o e-mail
            assunto = f'Boleto {id_cobranca} - ADV Assessoria'
            corpo = f'Prezados, segue anexo o boleto referente à cobrança {id_cobranca}.'
            enviar_email_boleto(
                destinatario=email_destinatario,
                assunto=assunto,
                corpo=corpo,
                anexo_path=pdf_filename,
                bcc='nortecheck-to@hotmail.com',
                nome_contato=nome_contato,
                nome_devedor=nome_devedor,
                data_vencimento=data_vencimento,
                valor_recebido=valor_recebido,
                valor_boleto=valor_boleto,
                percentual_boleto=percentual_boleto
            )
        else:
            print("Nenhum ID de cobrança foi retornado.")
    except Exception as e:
        print(f"Erro durante o processo: {e}")

def buscar_titulos_para_envio():
    """
    Busca os títulos de devedores para os quais o e-mail ainda não foi enviado.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)  # Usar dictionary=True para facilitar o acesso por nome da coluna

        query = """
        SELECT 
            id_cobranca,
            companies.email,
            titulo_devedor.valorRecebido, 
            titulo_devedor.updated_at,
            titulo_devedor.devedorId, 
            COALESCE(titulo_devedor.dataVencimentoReal, titulo_devedor.dataVencimento) AS dataVencimentoUtilizada,
            DATEDIFF(CURDATE(), COALESCE(titulo_devedor.dataVencimentoReal, titulo_devedor.dataVencimento)) AS dias_de_atraso,
            devedores.company_id, 
            titulo_devedor.email_enviado,  
            titulo_devedor.id AS id_titulo,
            companies.nome_contato AS contato_empresa,
            devedores.nome AS nome_devedor
        FROM 
            titulo_devedor
        JOIN 
            devedores ON titulo_devedor.devedorId = devedores.id
        JOIN 
            companies ON companies.id = devedores.company_id
        WHERE 
            titulo_devedor.statusBaixa = 2
            AND DATE(titulo_devedor.updated_at) = CURDATE()
            AND (titulo_devedor.email_enviado IS NULL OR titulo_devedor.email_enviado = 'NAO')
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            
            
def buscar_titulos_para_envio():
    """
    Busca os títulos de devedores para os quais o e-mail ainda não foi enviado.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)  # Usar dictionary=True para facilitar o acesso por nome da coluna

        query = """
        SELECT 
            id_cobranca,
            companies.email,
            titulo_devedor.valorRecebido, 
            titulo_devedor.updated_at,
            titulo_devedor.devedorId, 
            COALESCE(titulo_devedor.dataVencimentoReal, titulo_devedor.dataVencimento) AS dataVencimentoUtilizada,
            DATEDIFF(CURDATE(), COALESCE(titulo_devedor.dataVencimentoReal, titulo_devedor.dataVencimento)) AS dias_de_atraso,
            devedores.company_id, 
            titulo_devedor.email_enviado,  
            titulo_devedor.id AS id_titulo,
            companies.nome_contato AS contato_empresa,
            devedores.nome AS nome_devedor
        FROM 
            titulo_devedor
        JOIN 
            devedores ON titulo_devedor.devedorId = devedores.id
        JOIN 
            companies ON companies.id = devedores.company_id
        WHERE 
            titulo_devedor.statusBaixa = 2
            AND DATE(titulo_devedor.updated_at) = CURDATE()
            AND (titulo_devedor.email_enviado IS NULL OR titulo_devedor.email_enviado = 'NAO')
        """
        cursor.execute(query)
        results = cursor.fetchall()
        return results
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def atualizar_status_email_enviado(id_titulo):
    """
    Atualiza o campo email_enviado para 'SIM' após o envio do e-mail.
    """
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        query = "UPDATE titulo_devedor SET email_enviado = 'SIM' WHERE id = %s"
        cursor.execute(query, (id_titulo,))
        conn.commit()
        print(f"Status de e-mail atualizado para 'SIM' para o título ID {id_titulo}.")
    except mysql.connector.Error as err:
        print(f"Erro ao atualizar status de e-mail: {err}")
        raise
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def processar_titulos_para_envio():
    """
    Processa os títulos encontrados para envio de e-mails, envia e-mails e atualiza o status.
    """
    try:
        titulos = buscar_titulos_para_envio()
        if not titulos:
            print("Nenhum título encontrado para envio de e-mail.")
            return

        for titulo in titulos:
            id_titulo = titulo['id_titulo']
            id_cobranca = titulo['id_cobranca']

            if not id_cobranca:
                print(f"Erro: ID de cobrança está vazio ou inválido para o título ID {id_titulo}. Pulando...")
                continue

            email_destinatario = titulo['email']
            valor_recebido = titulo['valorRecebido']
            nome_devedor = titulo['nome_devedor']
            nome_contato = titulo['contato_empresa']
            data_vencimento = titulo['dataVencimentoUtilizada'].strftime("%d/%m/%Y")

            try:
                # Calcular o valor do boleto
                valor_boleto, dias_atraso, percentual_boleto = calcular_valor_boleto(valor_recebido, data_vencimento)

                # Baixar o boleto
                pdf_filename = baixar_boleto(id_cobranca)

                # Configurar e enviar o e-mail
                enviar_email_boleto(
                    destinatario=email_destinatario,
                    assunto=f'Boleto {id_cobranca} - ADV Assessoria',
                    corpo=f'Prezados, segue anexo o boleto referente à cobrança {id_cobranca}.',
                    anexo_path=pdf_filename,
                    bcc='nortecheck-to@hotmail.com',
                    nome_contato=nome_contato,
                    nome_devedor=nome_devedor,
                    data_vencimento=data_vencimento,
                    valor_recebido=valor_recebido,
                    valor_boleto=valor_boleto,
                    percentual_boleto=percentual_boleto
                )

                # Atualizar o status de envio de e-mail
                atualizar_status_email_enviado(id_titulo)

            except Exception as e:
                print(f"Erro ao processar título ID {id_titulo}: {e}")

    except Exception as e:
        print(f"Erro durante o processamento: {e}")

        
if __name__ == "__main__":
    processar_titulos_para_envio()

if __name__ == "__main__":
    main()
