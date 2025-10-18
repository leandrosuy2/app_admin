#!/bin/bash

# Defina as variáveis de conexão com o banco de dados
DB_HOST="xsender_db.mysql.dbaas.com.br"
DB_PORT="3306"
DB_NAME="xsender_db"
DB_USER="xsender_db"
DB_PASSWORD="Parceria@2020"

# Comando SQL para atualizar a tabela
SQL_COMMAND="DELETE FROM boletos;"


# Executa o comando SQL no banco de dados
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "$SQL_COMMAND"


# Verifica o status da execução
if [ $? -eq 0 ]; then
  echo "Update executado com sucesso!"
else
  echo "Erro ao executar o update."
fi

