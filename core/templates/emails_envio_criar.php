{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h1 class="text-center">Criar Novo E-mail de Envio</h1>
    
    <form method="POST">
        {% csrf_token %}
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" name="email" id="email" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="autenticacao">Autenticação</label>
            <select name="autenticacao" id="autenticacao" class="form-control">
                <option value="SSL">SSL</option>
                <option value="TLS">TLS</option>
            </select>
        </div>
        <div class="form-group">
            <label for="porta">Porta</label>
            <input type="number" name="porta" id="porta" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="servidor_smtp">Servidor SMTP</label>
            <input type="text" name="servidor_smtp" id="servidor_smtp" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="tipo_envio">Tipo de Envio</label>
            <select name="tipo_envio" id="tipo_envio" class="form-control">
                <option value="Quitação Parcela">Quitação Parcela</option>
                <option value="Quitação Contrato">Quitação Contrato</option>
                <option value="Nova Empresa">Nova Empresa</option>
                <option value="Negociação">Negociação</option>
				 <option value="Boleto">Boleto</option>
            </select>
        </div>
        <div class="form-group">
            <label for="provedor">Provedor</label>
            <input type="text" name="provedor" id="provedor" class="form-control" required>
        </div>
        <div class="form-group">
            <label for="senha">Senha</label>
            <input type="password" name="senha" id="senha" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary mt-3">Salvar</button>
    </form>
</div>
{% endblock %}