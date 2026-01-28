from django.contrib import admin
from .models import Word

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    # Відображаємо ці колонки у списку в адмінці
    list_display = ('english_word', 'ukrainian_translation', 'user', 'created_at')
    # Додаємо можливість фільтрації за користувачем
    list_filter = ('user',)