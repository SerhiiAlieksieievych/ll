from .models import Word, TextAnalysis
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
import re
from collections import Counter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import WordForm

# Перемикач статусу "Вивчено"
@login_required
def toggle_word_status(request, word_id):
    # Використовуємо правильну функцію
    word = get_object_or_404(Word, id=word_id, user=request.user)
    word.is_learned = not word.is_learned
    word.save()
    return redirect('word_list')

# Видалення слова
@login_required
def delete_word(request, word_id):
    word = get_object_or_404(Word, id=word_id, user=request.user)
    word.delete()
    return redirect('word_list')

# Редагування слова
@login_required
def edit_word(request, word_id):
    word = get_object_or_404(Word, id=word_id, user=request.user)
    if request.method == 'POST':
        form = WordForm(request.POST, instance=word)
        if form.is_valid():
            form.save()
            return redirect('word_list')
    else:
        form = WordForm(instance=word)
    return render(request, 'vocabulary/edit_word.html', {'form': form, 'word': word})

@login_required
def analyze_text(request):
    if request.method == 'POST':
        title = request.POST.get('title', 'Untitled')
        text = request.POST.get('text', '')

        # 1. Очищення тексту: тільки літери та пробіли, нижній регістр
        words_only = re.findall(r'\b[a-z]{2,}\b', text.lower())

        # 2. Підрахунок частоти
        frequency = Counter(words_only)

        # 3. Сортування за популярністю (від більшого до меншого)
        sorted_freq = dict(sorted(frequency.items(), key=lambda item: item[1], reverse=True))

        # 4. Збереження
        analysis = TextAnalysis.objects.create(
            user=request.user,
            title=title,
            original_text=text
        )
        analysis.set_frequency_data(sorted_freq)
        analysis.save()

        return redirect('view_analysis', analysis_id=analysis.id)

    return render(request, 'vocabulary/analyze_form.html')


@login_required
def view_analysis(request, analysis_id):
    analysis = TextAnalysis.objects.get(id=analysis_id, user=request.user)
    word_data = analysis.get_frequency_data()
    return render(request, 'vocabulary/analysis_result.html', {
        'analysis': analysis,
        'word_data': word_data
    })


@login_required
def add_word(request):
    if request.method == 'POST':
        form = WordForm(request.POST)
        if form.is_valid():
            word = form.save(commit=False)
            word.user = request.user
            word.source = 'manual' # Вказуємо джерело
            word.save()
            return redirect('word_list')
    else:
        form = WordForm()

    return render(request, 'vocabulary/add_word.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Зберігаємо юзера в базу
            login(request, user)  # Одразу авторизуємо його
            messages.success(request, "Реєстрація пройшла успішно!")
            return redirect('word_list')  # Перенаправляємо на список слів
    else:
        form = UserCreationForm()

    return render(request, 'vocabulary/register.html', {'form': form})
@login_required
def word_list(request):
    # Отримуємо слова лише того користувача, який авторизований
    words = Word.objects.filter(user=request.user)
    return render(request, 'vocabulary/index.html', {'words': words})


@login_required
def save_selected_words(request):
    if request.method == 'POST':
        selected_words = request.POST.getlist('selected_words')

        for word_en in selected_words:
            translation_ua = request.POST.get(f'translation_{word_en}')

            if translation_ua:
                Word.objects.create(
                    user=request.user,
                    english_word=word_en,
                    ukrainian_translation=translation_ua,
                    source='auto',
                    is_learned=False  # Явно вказуємо, що вони не вивчені
                )

        return redirect('word_list')