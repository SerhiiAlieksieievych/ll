from django import forms
from .models import Word

class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['english_word', 'ukrainian_translation']
        # Віджети додають класи Bootstrap до HTML-тегів, які генерує Django
        widgets = {
            'english_word': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: Adventure'
            }),
            'ukrainian_translation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Наприклад: Пригода'
            }),
        }
        # Також можна додати зрозумілі назви для полів (Labels)
        labels = {
            'english_word': 'Слово англійською',
            'ukrainian_translation': 'Переклад українською',
        }