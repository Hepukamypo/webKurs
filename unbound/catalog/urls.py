from django.urls import path
from . import views

urlpatterns = [
    path('',                           views.index,             name='index'),
    path('search/',                    views.search_view,       name='search'),

    # Игры
    path('game/<int:pk>/',             views.game_detail,       name='game_detail'),
    path('game/create/',               views.game_create,       name='game_create'),
    path('game/<int:pk>/edit/',        views.game_update,       name='game_update'),
    path('game/<int:pk>/delete/',      views.game_delete,       name='game_delete'),
    path('game/<int:pk>/buy/',         views.buy_game,          name='buy_game'),
    path('game/<int:pk>/download/',    views.game_download,     name='game_download'),
    path('game/<int:pk>/review/',      views.add_review,        name='add_review'),
    path('review/<int:pk>/delete/',    views.delete_review,     name='delete_review'),

    # Скриншоты
    path('game/<int:pk>/screenshot/add/',   views.screenshot_add,    name='screenshot_add'),
    path('screenshot/<int:pk>/delete/',     views.screenshot_delete, name='screenshot_delete'),

    # Достижения
    path('game/<int:game_pk>/achievement/create/', views.achievement_create, name='achievement_create'),
    path('achievement/<int:pk>/delete/',           views.achievement_delete, name='achievement_delete'),

    # Панель администратора
    path('dashboard/',                    views.dashboard,              name='dashboard'),
    path('dashboard/users/',              views.dashboard_users,        name='dashboard_users'),
    path('dashboard/achievements/',       views.dashboard_achievements, name='dashboard_achievements'),
    path('dashboard/purchases/',          views.dashboard_purchases,    name='dashboard_purchases'),

    # Модерация
    path('moderation/',                views.moderation,        name='moderation'),

    # Панель разработчика
    path('studio/',                       views.studio,               name='studio'),
    path('studio/game/create/',           views.studio_game_create,   name='studio_game_create'),
    path('studio/game/<int:pk>/edit/',    views.studio_game_update,   name='studio_game_update'),
    path('studio/game/<int:pk>/delete/',  views.studio_game_delete,   name='studio_game_delete'),
    path('studio/game/<int:pk>/publish/', views.studio_game_publish,  name='studio_game_publish'),

    # Аналитика студии
    path('studio/game/<int:pk>/analytics/', views.studio_analytics,   name='studio_analytics'),

    # Публичная страница разработчика
    path('developer/<str:username>/',       views.developer_page,     name='developer_page'),

    # Модерация игр
    path('games/moderation/',             views.game_moderation,      name='game_moderation'),
    path('games/<int:pk>/approve/',       views.game_approve,         name='game_approve'),
    path('games/<int:pk>/reject/',        views.game_reject,          name='game_reject'),

    # Сообщество
    path('community/',                    views.community,              name='community'),

    # Библиотека
    path('library/',                   views.library,           name='library'),

    # Аутентификация
    path('register/',                  views.register_view,     name='register'),

    # Профиль
    path('profile/<int:pk>/',          views.profile_view,      name='profile'),
    path('profile/edit/',              views.profile_edit,      name='profile_edit'),

    # Социальный модуль
    path('friend/request/<int:user_id>/',                      views.friend_request, name='friend_request'),
    path('friend/respond/<int:friendship_id>/<str:action>/',   views.friend_respond, name='friend_respond'),
    path('friend/remove/<int:user_id>/',                       views.friend_remove,  name='friend_remove'),
]
