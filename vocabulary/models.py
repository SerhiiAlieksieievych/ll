from django.db import models
from django.contrib.auth.models import User
import json

class TextAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    text = models.TextField()
    # Додаємо зв'язок зі словами
    words = models.ManyToManyField('Word', related_name='analyses', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def set_frequency_data(self, data):
        self.word_frequency_json = json.dumps(data)

    def get_frequency_data(self):
        return json.loads(self.word_frequency_json)


class Word(models.Model):
    # Варіанти джерела
    SOURCE_CHOICES = [
        ('manual', 'Вручну'),
        ('auto', 'Аналізатор'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    english_word = models.CharField(max_length=100)
    ukrainian_translation = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    # Нові поля
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
    is_learned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.english_word} - {self.ukrainian_translation}"