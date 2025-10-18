from django import forms
from .models import MensagemWhatsapp
from django.contrib.auth.hashers import make_password


class MensagemWhatsappForm(forms.ModelForm):
    class Meta:
        model = MensagemWhatsapp
        fields = ['mensagem', 'categoria']
        widgets = {
            'mensagem': forms.Textarea(attrs={'rows': 5, 'cols': 40, 'placeholder': 'Digite sua mensagem'}),
            'categoria': forms.Select(),
        }      