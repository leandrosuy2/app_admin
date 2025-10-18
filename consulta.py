import json
import pymysql
import re  # Para normalizar o CPF

# 🔹 Configuração do banco de dados
db_config = {
    "host": "127.0.0.1",
    "user": "admin",
    "password": "NovaSenha123",
    "database": "app_sistnortecheck",
    "charset": "utf8mb4",
}

def normalizar_cpf_cnpj(valor):
    """Remove caracteres especiais do CPF/CNPJ para garantir compatibilidade com o banco."""
    return re.sub(r'\D', '', valor)  # Remove tudo que não for número

@csrf_exempt
def salvar_dados_api_cadastro(request):
    if request.method == 'POST':
        # Obtendo CPF ou CNPJ do formulário
        cpf_cnpj = request.POST.get('cpf') or request.POST.get('cnpj')
        if not cpf_cnpj:
            return JsonResponse({'success': False, 'message': 'CPF ou CNPJ não fornecido.'})
        
        cpf_cnpj_normalizado = normalizar_cpf_cnpj(cpf_cnpj)
        
        try:
            # Conectando ao banco de dados
            with connection.cursor() as cursor:
                # Buscar os dados JSON da consulta usando cpfcnpj
                cursor.execute("SELECT consulta_data FROM consultas WHERE REPLACE(REPLACE(REPLACE(cpfcnpj, '.', ''), '-', ''), '/', '') = %s", [cpf_cnpj_normalizado])
                resultado = cursor.fetchone()
                
                if not resultado:
                    return JsonResponse({'success': False, 'message': 'Nenhum dado encontrado para a consulta.'})
                
                data = json.loads(resultado[0])
                cred_cadastral = data.get("CREDCADASTRAL", {})
                dados_receita = cred_cadastral.get("DADOS_RECEITA_FEDERAL", {})
                
                nome = dados_receita.get("NOME", "").strip()
                nome_mae = dados_receita.get("NOME_MAE", "").strip()
                
                # Coletar até 10 telefones
                telefones = []
                for tipo in ["TELEFONE_FIXO", "TELEFONE_CELULAR"]:
                    if tipo in cred_cadastral:
                        for tel in cred_cadastral[tipo].get("TELEFONES", []):
                            ddd = tel.get("DDD", "").strip()
                            numero = tel.get("NUM_TELEFONE", "").strip()
                            if ddd and numero:
                                telefones.append(f"({ddd}) {numero}")
                
                while len(telefones) < 10:
                    telefones.append(None)
                
                # Atualizar os dados do devedor
                update_query = """
                    UPDATE devedores
                    SET nome_socio = %s,
                        nome_mae = %s,
                        telefone1 = %s,
                        telefone2 = %s,
                        telefone3 = %s,
                        telefone4 = %s,
                        telefone5 = %s,
                        telefone6 = %s,
                        telefone7 = %s,
                        telefone8 = %s,
                        telefone9 = %s,
                        telefone10 = %s
                    WHERE REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), '/', '') = %s;
                """
                params = (nome, nome_mae, telefones[0], telefones[1], telefones[2], telefones[3], telefones[4],
                          telefones[5], telefones[6], telefones[7], telefones[8], telefones[9], cpf_cnpj_normalizado)
                
                cursor.execute(update_query, params)
                connection.commit()
                
                if cursor.rowcount > 0:
                    return JsonResponse({'success': True, 'message': 'Dados atualizados com sucesso!'})
                else:
                    return JsonResponse({'success': False, 'message': 'Nenhuma linha foi atualizada. O CPF/CNPJ pode não existir no banco.'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erro ao salvar dados: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Método inválido.'})

# Definição da rota
urlpatterns = [
    path('salvar_dados_api_cadastro/', salvar_dados_api_cadastro, name='salvar_dados_api_cadastro'),
]
