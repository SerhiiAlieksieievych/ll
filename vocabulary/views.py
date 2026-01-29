from .models import Word, TextAnalysis
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
import re
from collections import Counter
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import WordForm
from django.core.paginator import Paginator

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


import uuid


@login_required
def analyze_text(request):
    # Якщо просто зайшли на сторінку — чистимо все тимчасове
    if request.method == 'GET' and 'page' not in request.GET:
        request.session.pop('temp_analysis_data', None)
        return render(request, 'vocabulary/analyze_form.html')

    if request.method == 'POST':
        title = request.POST.get('title')
        raw_text = request.POST.get('text')

        # Зберігаємо дані в сесію як "тимчасові"
        request.session['temp_analysis_data'] = {
            'title': title,
            'text': raw_text,
        }
        return redirect('analyze_text')

    # Отримуємо дані з сесії
    temp_data = request.session.get('temp_analysis_data')
    if not temp_data:
        return redirect('analyze_text')

    raw_text = temp_data['text']
    title = temp_data['title']

    # --- Твій стандартний аналіз слів ---
    words_in_text = re.findall(r'\b\w+\b', raw_text.lower())
    raw_word_counts = Counter(words_in_text)
    existing_words = set(Word.objects.filter(user=request.user).values_list('english_word', flat=True))

    new_words = []
    hidden_words = []
    for word, count in raw_word_counts.items():
        if not word.isdigit() and len(word) > 1:
            if word in existing_words:
                hidden_words.append({'word': word, 'count': count})
            else:
                new_words.append({'word': word, 'count': count})

    new_words.sort(key=lambda x: x['count'], reverse=True)

    paginator = Paginator(new_words, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'vocabulary/analysis_result.html', {
        'page_obj': page_obj,
        'title': title,
        'raw_text': raw_text,  # Передаємо текст, щоб його можна було зберегти
        'hidden_words': hidden_words,
        'skipped_count': len(hidden_words),
        'is_temp': True  # Прапор, що текст ще не в базі
    })


# НОВА функція для фактичного збереження
@login_required
def save_analysis(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')

        # Створюємо запис у бібліотеці
        analysis = TextAnalysis.objects.create(
            user=request.user,
            title=title,
            text=text
        )
        # Можна додати повідомлення "Текст збережено"
        return redirect('view_analysis', pk=analysis.pk)
    return redirect('analysis_list')

@login_required
def delete_analysis(request, pk):
    analysis = get_object_or_404(TextAnalysis, pk=pk, user=request.user)
    if request.method == 'POST':
        analysis.delete()
    return redirect('analysis_list')


@login_required
def view_analysis(request, analysis_id):
    analysis = get_object_or_404(TextAnalysis, id=analysis_id, user=request.user)

    # 1. Розбиваємо текст аналізу на слова
    words_in_text = set(re.findall(r'\b\w+\b', analysis.text.lower()))

    # 2. Динамічно шукаємо ці слова у словнику користувача
    # Ми беремо всі слова користувача, які є в цьому тексті
    user_vocabulary = Word.objects.filter(
        user=request.user,
        english_word__in=words_in_text
    )

    return render(request, 'vocabulary/view_analysis.html', {
        'analysis': analysis,
        'vocabulary': user_vocabulary,
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
        analysis_id = request.POST.get('analysis_id')

        # Перевіряємо, чи є ID і чи це число
        if not analysis_id or not analysis_id.isdigit():
            # Якщо ID немає, просто перенаправляємо назад
            return redirect('word_list')

        analysis = get_object_or_404(TextAnalysis, id=analysis_id, user=request.user)

        for word_en in selected_words:
            translation_ua = request.POST.get(f'translation_{word_en}', '').strip()

            word_obj, created = Word.objects.get_or_create(
                user=request.user,
                english_word=word_en.lower(),
                defaults={'ukrainian_translation': translation_ua}
            )
            analysis.words.add(word_obj)

    return redirect('word_list')


@login_required
def analysis_list(request):
    # Отримуємо всі аналізи користувача, від нових до старих
    analyses = TextAnalysis.objects.filter(user=request.user).order_order_by('-created_at')
    return render(request, 'vocabulary/analysis_list.html', {'analyses': analyses})


@login_required
def view_analysis(request, pk):
    # Отримуємо конкретний аналіз
    analysis = get_object_or_404(TextAnalysis, pk=pk, user=request.user)

    # Отримуємо всі слова, які ПРИВ'ЯЗАНІ саме до цього тексту
    # Це і є наш "словник тексту"
    words = analysis.words.all().order_by('english_word')

    return render(request, 'vocabulary/view_analysis.html', {
        'analysis': analysis,
        'words': words
    })

@login_required
def analysis_list(request):
    analyses = TextAnalysis.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'vocabulary/analysis_list.html', {'analyses': analyses})

@login_required
def view_analysis(request, pk):
    analysis = get_object_or_404(TextAnalysis, pk=pk, user=request.user)
    # Отримуємо слова, які належать ЦЬОМУ тексту (через ManyToMany)
    # Але також перевіряємо їх актуальний переклад зі словника користувача
    words = analysis.words.all()
    return render(request, 'vocabulary/view_analysis.html', {
        'analysis': analysis,
        'words': words
    })