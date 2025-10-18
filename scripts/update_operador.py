import mysql.connector
import random

# Configurações de conexão com o banco de dados
DB_HOST = "xsender_db.mysql.dbaas.com.br"
DB_PORT = 3306
DB_NAME = "xsender_db"
DB_USER = "xsender_db"
DB_PASSWORD = "Parceria@2020"

try:
    # Conectar ao banco de dados
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()

    # Limpar o campo operador em devedores que não possuem registros em agendamentos
    print("Resetando campo operador para devedores sem agendamentos...")
    cursor.execute("""
        UPDATE devedores
        SET operador = NULL
        WHERE id NOT IN (SELECT DISTINCT devedor_id FROM agendamentos)
          AND (statusBaixa IN (0, 1) OR statusBaixa IS NULL)
    """)
    conn.commit()
    print("Campo operador resetado para devedores sem agendamentos com sucesso!")

    # Obter todos os usernames dos operadores
    print("Obtendo operadores...")
    cursor.execute("SELECT username FROM operadors")
    operators = [row[0] for row in cursor.fetchall()]

    if not operators:
        print("Nenhum operador encontrado.")
        exit()

    # Obter IDs dos devedores que atendem aos critérios
    print("Obtendo devedores disponíveis...")
    cursor.execute("""
        SELECT id FROM devedores
        WHERE statusBaixa IS NULL
          AND operador IS NULL
    """)
    devedores_ids = [row[0] for row in cursor.fetchall()]

    if not devedores_ids:
        print("Nenhum devedor disponível.")
        exit()

    # Atualizar devedores com operadores aleatórios
    print("Atualizando operadores para devedores...")
    for operator in operators:
        random_devedores = random.sample(devedores_ids, min(30, len(devedores_ids)))
        for devedor_id in random_devedores:
            cursor.execute(
                "UPDATE devedores SET operador = %s WHERE id = %s",
                (operator, devedor_id)
            )
            devedores_ids.remove(devedor_id)  # Garantir que IDs não sejam reutilizados

    # Confirmar as alterações no banco de dados
    conn.commit()
    print("Operadores atualizados com sucesso!")

except mysql.connector.Error as err:
    print(f"Erro ao conectar ou executar no banco de dados: {err}")

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()

