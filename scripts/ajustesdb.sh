#!/bin/bash

# Defina as variáveis de conexão com o banco de dados
DB_HOST="xsender_db.mysql.dbaas.com.br"
DB_PORT="3306"
DB_NAME="xsender_db"
DB_USER="xsender_db"
DB_PASSWORD="Parceria@2020"

# Comando SQL para atualizar a tabela
SQL_COMMAND="UPDATE titulo_devedor SET dataVencimentoReal = dataVencimento, dataVencimentoPrimeira=dataVencimento WHERE dataVencimentoReal IS NULL and statusBaixa=2;"

SQL_COMMAND2="update devedores set nome=nome_fantasia where nome is null or nome = '' and cnpj is not null;"

# Comando SQL para atualizar operador na tabela devedores
#SQL_COMMAND3="
#UPDATE devedores
#SET operador = (
#    SELECT agendamentos.operador
#    FROM agendamentos
#    WHERE agendamentos.devedor_id = devedores.id
#      AND agendamentos.operador IS NOT NULL
#    ORDER BY agendamentos.id DESC
#    LIMIT 1
#)
#WHERE devedores.statusBaixa IN (0, 1) OR devedores.statusBaixa IS NULL;
#"

# Comando SQL para calcular e atualizar os juros
SQL_COMMAND_CALC_JUROS="
UPDATE titulo_devedor
SET juros = ROUND((DATEDIFF(CURDATE(), dataVencimento) / 30) * 0.08 * valor, 2)
WHERE (statusBaixa IS NULL OR statusBaixa = 0) AND dataVencimento < CURDATE();
"


# Executa o comando SQL no banco de dados
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$SQL_COMMAND"
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$SQL_COMMAND2"
#mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$SQL_COMMAND3"
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$SQL_COMMAND_CALC_JUROS"


# Verifica o status da execução
if [ $? -eq 0 ]; then
  echo "Update executado com sucesso!"
else
  echo "Erro ao executar o update."
fi

