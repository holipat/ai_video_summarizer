from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.user_login, name='login'),
    path('signup', views.user_signup, name='signup'),
    path('logout', views.user_logout, name='logout'),
    path('generate-article', views.generate_article, name='generate-article'),
    path('article-list', views.article_list, name='article-list'),
    path('article-details/<int:pk>/', views.article_details, name='article-details'),
]