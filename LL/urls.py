from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Кастомний вхід та вихід
    path('accounts/login/', auth_views.LoginView.as_view(template_name='vocabulary/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ПОВНІСТЮ КАСИОМНИЙ ШЛЯХ ДЛЯ ПАРОЛЯ
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(
        # Вкажіть тут точний шлях до перейменованого файлу
        template_name='vocabulary/password_change_custom.html',
        success_url='/profile/'
    ), name='password_change'),

    # Всі інші системні URL
    path('accounts/', include('django.contrib.auth.urls')),

    path('', include('vocabulary.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)