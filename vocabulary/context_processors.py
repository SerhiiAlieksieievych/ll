from .models import Word

def global_stats(request):
    if request.user.is_authenticated:
        return {
            'navbar_word_count': Word.objects.filter(user=request.user).count()
        }
    return {'navbar_word_count': 0}