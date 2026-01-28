from django.urls import path
from . import views

urlpatterns = [
    path('', views.word_list, name='word_list'),
    path('register/', views.register, name='register'),
    path('add/', views.add_word, name='add_word'),
    path('analyze/', views.analyze_text, name='analyze_text'),
    path('analysis/<int:analysis_id>/', views.view_analysis, name='view_analysis'),
    path('save-selected/', views.save_selected_words, name='save_selected_words'),
    path('toggle/<int:word_id>/', views.toggle_word_status, name='toggle_word_status'),
    path('delete/<int:word_id>/', views.delete_word, name='delete_word'),
    path('edit/<int:word_id>/', views.edit_word, name='edit_word'),
]