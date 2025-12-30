from django import forms
from django.utils import timezone
from .models import DailySale

class DailySaleForm(forms.ModelForm):
    """Formulário para lançamento de venda diária."""
    
    date = forms.DateField(
        label="Data da Venda",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now
    )
    
    amount = forms.DecimalField(
        label="Valor Total (R$)",
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '0,00',
            'step': '0.01'
        })
    )
    
    notes = forms.CharField(
        label="Observações (Opcional)",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = DailySale
        fields = ['date', 'amount', 'notes']

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.now().date():
            raise forms.ValidationError("Não é permitido lançar vendas para o futuro.")
        return date
