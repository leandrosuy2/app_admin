from django import forms
from .models import MensagemWhatsapp, TemplateMensagemWhatsapp
from django.contrib.auth.hashers import make_password


class MensagemWhatsappForm(forms.ModelForm):
    class Meta:
        model = MensagemWhatsapp
        fields = ['mensagem', 'categoria']
        widgets = {
            'mensagem': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'placeholder': 'Digite sua mensagem'}),
            'categoria': forms.Select(),
        }


class TemplateMensagemWhatsappForm(forms.ModelForm):
    class Meta:
        model = TemplateMensagemWhatsapp
        fields = ['nome', 'categoria', 'template_mensagem', 'follow_up_automatico', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do template'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'template_mensagem': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 15, 
                'placeholder': 'Digite o template da mensagem com variáveis'
            }),
            'follow_up_automatico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }      