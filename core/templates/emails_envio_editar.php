{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h1 class="text-center">Editar E-mail de Envio</h1>
    
    <form method="POST">
        {% csrf_token %}
        <div class="form-group">
            <label for="email">Email</label>
            <input type="email" name="email" id="email" class="form-control" value="{{ email_envio.email }}" required>
        </div>
        <div class="form-group">
            <label for="autenticacao">Autenticação</label>
            <select name="autenticacao" id="autenticacao" class="form-control">
                <option value="SSL" {% if email_envio.autenticacao == 'SSL' %}selected{% endif %}>SSL</option>
                <option value="TLS" {% if email_envio.autenticacao == 'TLS' %}selected{% endif %}>TLS</option>
            </select>
        </div>
        <div class="form-group">
            <label for="porta">Porta</label>
            <input type="number" name="porta" id="porta" class="form-control" value="{{ email_envio.porta }}" required>
        </div>
        <div class="form-group">
            <label for="servidor_smtp">Servidor SMTP</label>
            <input type="text" name="servidor_smtp" id="servidor_smtp" class="form-control" value="{{ email_envio.servidor_smtp }}" required>
        </div>
        <div class="form-group">
			<label for="tipo_envio">Tipo de Envio</label>
			<select name="tipo_envio" id="tipo_envio" class="form-control">
				<option value="Quitação Parcela" {% if email_envio.tipo_envio == 'Quitação Parcela' %}selected{% endif %}>Quitação Parcela</option>
				<option value="Quitação Contrato" {% if email_envio.tipo_envio == 'Quitação Contrato' %}selected{% endif %}>Quitação Contrato</option>
				<option value="Nova Empresa" {% if email_envio.tipo_envio == 'Nova Empresa' %}selected{% endif %}>Nova Empresa</option>
				<option value="Negociação" {% if email_envio.tipo_envio == 'Negociação' %}selected{% endif %}>Negociação</option>
			</select>
		</div>
        <div class="form-group">
            <label for="provedor">Provedor</label>
            <input type="text" name="provedor" id="provedor" class="form-control" value="{{ email_envio.provedor }}" required>
        </div>
        <div class="form-group">
            <label for="senha">Senha</label>
            <input type="password" name="senha" id="senha" class="form-control" required>
        </div>
        <button type="submit" class="btn btn-primary mt-3">Atualizar</button>
    </form>
</div>
{% endblock %}


