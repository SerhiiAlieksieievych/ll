from django import forms
from .models import Word

class WordForm(forms.ModelForm):
    class Meta:
        model = Word
        fields = ['english_word', 'ukrainian_translation']
        widgets = {
            'english_word': forms.TextInput(attrs={'class': 'form-control'}),
            'ukrainian_translation': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # Метод для обробки англійського слова
    def clean_english_word(self):
        word = self.cleaned_data.get('english_word')
        return word.lower().strip() if word else word

    # Метод для обробки перекладу
    def clean_ukrainian_translation(self):
        translation = self.cleaned_data.get('ukrainian_translation')
        return translation.lower().strip() if translation else translation
        # Також можна додати зрозумілі назви для полів (Labels)

    labels = {
        'english_word': 'Слово англійською',
        'ukrainian_translation': 'Переклад українською',
    }