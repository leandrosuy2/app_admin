import mysql.connector
import requests
from datetime import datetime, timedelta

# Configuração da API do Banco Inter
api_config = {
    'cert_path': '/home/app_admin/core/certificados/Inter_API_Certificado.crt',
    'key_path': '/home/app_admin/core/certificados/Inter_API_Chave.key',
    'token_url': 'https://cdpj.partners.bancointer.com.br/oauth/v2/token',
    'cobrancas_url': 'https://cdpj.partners.bancointer.com.br/cobranca/v3/cobrancas',
    'client_id': '28e744c0-0d81-4110-8d24-76accfce8f62',
    'client_secret': 'd49b790d-2172-4838-bbb0-966dd9209903',
    'conta_corrente': '49289195'  # Substitua pelo número correto da conta
}

# Configuração do banco de dados
db_config = {
    'host': 'localhost',
    'user': 'advassessoria',
    'password': 'Parceria@2025!',
    'database': 'app',
}

def obter_token():
    """
    Obtém o token de acesso da API do Banco Inter.
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
        raise

def listar_cobrancas(data_inicial, data_final, situacoes=None):
    """
    Lista todas as cobranças entre as datas especificadas e opcionalmente por situações.
    """
    token = obter_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "x-conta-corrente": api_config['conta_corrente']
    }
    params = {
        "dataInicial": data_inicial,
        "dataFinal": data_final,
        "filtrarDataPor": "VENCIMENTO",
        "paginacao.itensPorPagina": 100,
        "paginacao.paginaAtual": 0
    }

    todas_cobrancas = []

    while True:
        try:
            # Se houver situações especificadas, itera sobre elas
            if situacoes:
                for situacao in situacoes:
                    params["situacao"] = situacao

                    response = requests.get(
                        api_config['cobrancas_url'],
                        headers=headers,
                        params=params,
                        cert=(api_config['cert_path'], api_config['key_path'])
                    )
                    response.raise_for_status()

                    data = response.json()
                    print("Resposta da API:", data)

                    cobrancas = data.get("cobrancas", [])
                    if not cobrancas:
                        print(f"Nenhuma cobrança encontrada para a situação: {situacao}")
                        continue

                    todas_cobrancas.extend(cobrancas)

            # Se não houver mais páginas ou situações, sair do loop
            if data.get("ultimaPagina", True):
                break

            params["paginacao.paginaAtual"] += 1
        except requests.RequestException as e:
            print(f"Erro ao listar cobranças: {e}")
            raise

    return todas_cobrancas

def salvar_boleto_no_banco(cobranca):
    """
    Salva ou atualiza um boleto no banco de dados.
    """
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        sql = """
        INSERT INTO core_boleto (
            codigo_solicitacao,
            seu_numero,
            situacao,
            data_situacao,
            data_emissao,
            data_vencimento,
            valor_nominal,
            valor_total_recebido,
            origem_recebimento,
            pagador_nome,
            pagador_cpf_cnpj,
            nosso_numero,
            linha_digitavel,
            codigo_barras,
            txid
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE 
            situacao = VALUES(situacao),
            data_situacao = VALUES(data_situacao),
            valor_total_recebido = VALUES(valor_total_recebido),
            origem_recebimento = VALUES(origem_recebimento),
            atualizado_em = CURRENT_TIMESTAMP;
        """

        cobranca_dados = cobranca.get('cobranca', {})
        boleto_dados = cobranca.get('boleto', {})
        pix_dados = cobranca.get('pix', {})

        cursor.execute(sql, (
            cobranca_dados.get("codigoSolicitacao"),
            cobranca_dados.get("seuNumero"),
            cobranca_dados.get("situacao"),
            cobranca_dados.get("dataSituacao"),
            cobranca_dados.get("dataEmissao"),
            cobranca_dados.get("dataVencimento"),
            cobranca_dados.get("valorNominal"),
            cobranca_dados.get("valorTotalRecebido"),
            cobranca_dados.get("origemRecebimento"),
            cobranca_dados.get("pagador", {}).get("nome"),
            cobranca_dados.get("pagador", {}).get("cpfCnpj"),
            boleto_dados.get("nossoNumero"),
            boleto_dados.get("linhaDigitavel"),
            boleto_dados.get("codigoBarras"),
            pix_dados.get("txid")
        ))

        connection.commit()
        print(f"Boleto salvo ou atualizado: {cobranca_dados.get('codigoSolicitacao')}")

    except mysql.connector.Error as e:
        print(f"Erro ao salvar boleto no banco de dados: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def main():
    # Configurar intervalo de datas para os últimos 30 dias
    data_inicial = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    data_final = datetime.now().strftime("%Y-%m-%d")

    # Situações desejadas
    situacoes_desejadas = ["A_RECEBER", "ATRASADO", "RECEBIDO"]

    print(f"Listando cobranças de {data_inicial} a {data_final} nas situações {situacoes_desejadas}...")

    try:
        cobrancas = listar_cobrancas(data_inicial, data_final, situacoes_desejadas)

        if not cobrancas:
            print("Nenhuma cobrança encontrada no período especificado.")
            return

        print(f"Total de cobranças encontradas: {len(cobrancas)}")
        for cobranca in cobrancas:
            salvar_boleto_no_banco(cobranca)

    except Exception as e:
        print(f"Erro durante a listagem de cobranças: {e}")


if __name__ == "__main__":
    main()
