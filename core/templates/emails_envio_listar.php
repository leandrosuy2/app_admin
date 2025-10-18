{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h1 class="text-center mb-4 fw-bold" style="font-size: 26px; color: #2c3e50; text-transform: uppercase; letter-spacing: 1px;">
        <i class="fas fa-envelope me-2" style="color: #34495e;"></i> Lista de E-mails de Envio
    </h1>
    
    <!-- Botão para adicionar novo e-mail -->
    <div class="d-flex justify-content-end mb-3">
        <a href="{% url 'emails_envio_criar' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Adicionar E-mail
        </a>
    </div>
    
    <table class="table table-hover table-bordered align-middle">
        <thead class="table-dark">
            <tr>
                <th>Email</th>
                <th>Autenticação</th>
                <th>Porta</th>
                <th>Servidor SMTP</th>
                <th>Tipo de Envio</th>
                <th>Provedor</th>
                <th class="text-center">Ações</th>
            </tr>
        </thead>
        <tbody>
            {% for email in emails %}
            <tr>
                <td>{{ email.email }}</td>
                <td>{{ email.get_autenticacao_display }}</td>
                <td>{{ email.porta }}</td>
                <td>{{ email.servidor_smtp }}</td>
                <td>{{ email.get_tipo_envio_display }}</td>
                <td>{{ email.provedor }}</td>
                <td class="text-center">
                    <a href="{% url 'emails_envio_editar' email.id %}" class="btn btn-sm btn-warning">Editar</a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
