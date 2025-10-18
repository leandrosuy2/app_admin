#!/usr/bin/env python3

import requests
import pymysql
import re

# Configurações do Banco de Dados
DB_CONFIG = {
    'host': 'xsender_db.mysql.dbaas.com.br',
    'user': 'xsender_db',
    'password': 'Parceria@2020',
    'database': 'xsender_db',
    'charset': 'latin1'
}

# Configurações da API
ACCESS_TOKEN = 'h2XxFszVMoRgjQCBkn5WejKDmor2BNl5I2ko1i4q'
API_BASE_URL = 'https://api.lemit.com.br/api/v1/consulta'


def buscar_devedores():
    """
    Busca IDs de devedores que atendem às condições e ainda não foram consultados.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = """
            SELECT id FROM devedores
            WHERE (statusBaixa IS NULL OR statusBaixa = 0)
              AND (telefone1 IS NULL OR telefone1 LIKE '%9999%')
              AND (telefone2 IS NULL OR telefone2 LIKE '%9999%')
              AND (telefone3 IS NULL OR telefone3 LIKE '%9999%')
              AND (telefone4 IS NULL OR telefone4 LIKE '%9999%')
              AND (telefone5 IS NULL OR telefone5 LIKE '%9999%')
              AND (telefone6 IS NULL OR telefone6 LIKE '%9999%')
              AND (telefone7 IS NULL OR telefone7 LIKE '%9999%')
              AND (telefone8 IS NULL OR telefone8 LIKE '%9999%')
              AND (telefone9 IS NULL OR telefone9 LIKE '%9999%')
              AND (telefone10 IS NULL OR telefone10 LIKE '%9999%')
              AND id NOT IN (SELECT devedor_id FROM consultados_api)
        """
        cursor.execute(query)
        devedores = cursor.fetchall()

        return [devedor['id'] for devedor in devedores]

    except pymysql.MySQLError as db_err:
        print(f"Erro no banco de dados ao buscar devedores: {db_err}")
        return []
    finally:
        if conn:
            conn.close()


def registrar_consulta(devedor_id, status):
    """
    Registra o resultado da consulta na tabela consultados_api.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO consultados_api (devedor_id, status_consulta)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE status_consulta = VALUES(status_consulta), data_consulta = CURRENT_TIMESTAMP
        """, (devedor_id, status))
        conn.commit()

    except pymysql.MySQLError as db_err:
        print(f"Erro ao registrar consulta para devedor ID {devedor_id}: {db_err}")
    finally:
        if conn:
            conn.close()


def consultar_api(devedor_id):
    """
    Consulta a API e atualiza os telefones e o nome da mãe do devedor no banco de dados.
    """
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # Obter informações do devedor
        cursor.execute("SELECT id, cpf, cnpj, nome, nome_mae FROM devedores WHERE id = %s", (devedor_id,))
        devedor = cursor.fetchone()

        if not devedor:
            print(f"Devedor com ID {devedor_id} não encontrado.")
            return

        cpf = re.sub(r'\D', '', devedor['cpf']) if devedor['cpf'] else None
        cnpj = re.sub(r'\D', '', devedor['cnpj']) if devedor['cnpj'] else None

        # Determinar o endpoint correto
        if cpf:
            url = f'{API_BASE_URL}/pessoa/{cpf}'
        elif cnpj:
            url = f'{API_BASE_URL}/empresa/{cnpj}'
        else:
            print(f"Devedor ID {devedor_id} não possui CPF ou CNPJ.")
            return

        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Consultar a API
        response = requests.get(url, headers=headers)

        if response.status_code == 404:
            print(f"Devedor ID {devedor_id}: CPF/CNPJ não encontrado na API.")
            registrar_consulta(devedor_id, 'failure')  # Registra consulta com falha
            return

        response.raise_for_status()
        api_data = response.json()
        pessoa_data = api_data.get('pessoa', api_data.get('empresa', {}))

        # Atualizar campos no banco de dados
        phones = [
            f"{p['ddd']}{p['numero']}" for p in pessoa_data.get('celulares', []) + pessoa_data.get('fixos', [])
        ][:10]  # Máximo de 10 telefones
        phones += [None] * (10 - len(phones))  # Preencher campos restantes com NULL

        update_query = """
            UPDATE devedores
            SET nome = %s, nome_mae = %s, telefone1 = %s, telefone2 = %s, telefone3 = %s,
                telefone4 = %s, telefone5 = %s, telefone6 = %s, telefone7 = %s, telefone8 = %s,
                telefone9 = %s, telefone10 = %s
            WHERE id = %s
        """
        cursor.execute(update_query, (
            pessoa_data.get('nome', devedor['nome']),
            pessoa_data.get('nome_mae', devedor['nome_mae']),
            *phones,
            devedor_id
        ))
        conn.commit()

        print(f"Devedor ID {devedor_id} atualizado com sucesso.")
        registrar_consulta(devedor_id, 'success')  # Registra consulta bem-sucedida

    except requests.exceptions.HTTPError as http_err:
        print(f"Erro na API para devedor ID {devedor_id}: {http_err}. Resposta: {response.text}")
        registrar_consulta(devedor_id, 'failure')  # Registra consulta com falha
    except pymysql.MySQLError as db_err:
        print(f"Erro no banco de dados para devedor ID {devedor_id}: {db_err}")
    except Exception as e:
        print(f"Erro inesperado para devedor ID {devedor_id}: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    devedor_ids = buscar_devedores()
    if not devedor_ids:
        print("Nenhum devedor encontrado para atualizar.")
    else:
        for devedor_id in devedor_ids:
            consultar_api(devedor_id)
