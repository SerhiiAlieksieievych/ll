from .models import Word, TextAnalysis, TextWord
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
    # 1. Якщо це просто перехід з навбара — показуємо чисту форму
    if request.method == 'GET' and 'page' not in request.GET:
        request.session.pop('temp_analysis_data', None)
        return render(request, 'vocabulary/analyze_form.html')

    # 2. Отримуємо дані (або з POST, або з сесії для пагінації)
    if request.method == 'POST':
        title = request.POST.get('title', 'Без назви')
        raw_text = request.POST.get('text', '')
        # Зберігаємо в сесію ТІЛЬКИ для того, щоб працювала пагінація (перехід по сторінках)
        request.session['temp_analysis_data'] = {'title': title, 'text': raw_text}
    else:
        temp_data = request.session.get('temp_analysis_data')
        if not temp_data:
            return redirect('analyze_text')
        title = temp_data.get('title')
        raw_text = temp_data.get('text')

    if not raw_text:
        return redirect('analyze_text')

    # 3. САМ АНАЛІЗ (Regex + Counter)
    words_in_text = re.findall(r'\b\w+\b', raw_text.lower())
    raw_word_counts = Counter(words_in_text)

    # Отримуємо існуючі слова користувача
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

    # 4. ПАГІНАЦІЯ
    paginator = Paginator(new_words, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vocabulary/analysis_result.html', {
        'page_obj': page_obj,
        'title': title,
        'raw_text': raw_text,
        'hidden_words': hidden_words,
        'skipped_count': len(hidden_words),
        'is_temp': True
    })


# НОВА функція для фактичного збереження
@login_required
def save_analysis(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        text = request.POST.get('text')

        # 1. Створюємо аналіз
        analysis = TextAnalysis.objects.create(
            user=request.user,
            title=title,
            text=text
        )

        # 2. Отримуємо дані аналізу з сесії (ті самі, що бачив користувач)
        temp_data = request.session.get('temp_analysis_data')
        if temp_data:
            # Повторюємо швидкий аналіз для отримання count
            words_in_text = re.findall(r'\b\w+\b', text.lower())
            word_counts = Counter(words_in_text)

            # 3. Зберігаємо КОЖНЕ слово в словник тексту
            text_words = []
            for word, count in word_counts.items():
                if not word.isdigit() and len(word) > 1:
                    # Шукаємо, чи є вже переклад у загальному словнику, щоб підставити автоматично
                    existing_word = Word.objects.filter(user=request.user, english_word=word).first()
                    trans = existing_word.ukrainian_translation if existing_word else ""

                    text_words.append(TextWord(
                        analysis=analysis,
                        word=word,
                        count=count,
                        translation=trans
                    ))

            # Масове збереження для швидкості
            TextWord.objects.bulk_create(text_words)

        request.session.pop('temp_analysis_data', None)
        return redirect('view_analysis', pk=analysis.pk)

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
    all_words = Word.objects.filter(user=request.user)

    total_count = all_words.count()
    # Рахуємо тільки ті, де is_learned=False
    unlearned_count = all_words.filter(is_learned=False).count()

    return render(request, 'vocabulary/index.html', {
        'words': all_words,
        'total_count': total_count,
        'unlearned_count': unlearned_count,
    })


@login_required
def save_selected_words(request):
    if request.method == 'POST':
        # Отримуємо список слів (тих, де стоять галочки)
        selected_words = request.POST.getlist('selected_words')
        analysis_id = request.POST.get('analysis_id')

        for word_en in selected_words:
            # Дістаємо переклад саме для цього слова
            translation_ua = request.POST.get(f'translation_{word_en}', '').strip()

            # Створюємо або оновлюємо слово в словнику користувача
            word_obj, created = Word.objects.update_or_create(
                user=request.user,
                english_word=word_en.lower(),
                defaults={'ukrainian_translation': translation_ua.lower()},
                source="auto"
            )

            # Якщо ми в процесі перегляду збереженого тексту (є ID) — додаємо зв'язок
            if analysis_id and analysis_id.isdigit():
                analysis = get_object_or_404(TextAnalysis, id=analysis_id, user=request.user)
                analysis.words.add(word_obj)

        return redirect('word_list')

    return redirect('analyze_text')


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

    # 1. Отримуємо всі слова цього тексту
    all_text_words = analysis.text_vocabulary.all().order_by('-count')

    # 2. Отримуємо список усіх слів, які користувач ВЖЕ вивчив (з основного словника)
    user_learned_words = set(
        Word.objects.filter(user=request.user).values_list('english_word', flat=True)
    )

    new_words = []
    hidden_words = []

    # 3. Розподіляємо слова
    for item in all_text_words:
        word_data = {
            'word': item.word,
            'count': item.count,
            'translation': item.translation
        }
        if item.word in user_learned_words:
            hidden_words.append(word_data)
        else:
            new_words.append(word_data)

    # 4. Пагінація для нових слів (якщо їх багато)
    paginator = Paginator(new_words, 50)  # Збільшимо ліміт для зручності
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'vocabulary/view_analysis.html', {
        'analysis': analysis,
        'page_obj': page_obj,
        'hidden_words': hidden_words,
        'skipped_count': len(hidden_words),
    })

@login_required
def toggle_word_learned(request, pk):
    word = get_object_or_404(Word, pk=pk, user=request.user)
    word.is_learned = not word.is_learned
    word.save()
    return redirect(request.META.get('HTTP_REFERER', 'word_list'))