from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.db.models import Avg, Count, Sum, Q
from functools import wraps

from .models import (Game, Achievement, UserAchievement,
                     Purchase, Review, Friendship, User, Screenshot)
from .forms import (RegisterForm, GameForm, ReviewForm,
                    ProfileForm, ScreenshotForm, AchievementForm)


# ── Декораторы ────────────────────────────────────────────────────────────────

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin():
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def developer_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_developer() or request.user.is_admin()):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


# ── Система достижений ────────────────────────────────────────────────────────

def unlock_achievement(user, achievement):
    _, created = UserAchievement.objects.get_or_create(
        user=user, achievement=achievement)
    return created


def check_and_unlock(user, trigger, game=None):
    unlocked = []
    if game and trigger in ('buy_game', 'write_review'):
        for ach in Achievement.objects.filter(game=game, trigger=trigger):
            if unlock_achievement(user, ach):
                unlocked.append(ach)
    if trigger == 'buy_game':
        total_purchases = Purchase.objects.filter(user=user).count()
        for trig, threshold in [('buy_any_3', 3), ('buy_any_5', 5), ('buy_any_10', 10)]:
            if total_purchases >= threshold:
                for ach in Achievement.objects.filter(trigger=trig):
                    if unlock_achievement(user, ach):
                        unlocked.append(ach)
    if trigger == 'write_review':
        total_reviews = Review.objects.filter(user=user).count()
        for trig, threshold in [('write_any_3', 3), ('write_any_5', 5)]:
            if total_reviews >= threshold:
                for ach in Achievement.objects.filter(trigger=trig):
                    if unlock_achievement(user, ach):
                        unlocked.append(ach)
    if trigger == 'add_friend':
        for ach in Achievement.objects.filter(trigger='add_friend'):
            if unlock_achievement(user, ach):
                unlocked.append(ach)
    return unlocked


# ── Каталог ───────────────────────────────────────────────────────────────────

def index(request):
    genre = request.GET.get('genre', '')
    sort  = request.GET.get('sort', '-created_at')
    games = Game.objects.filter(status='published').annotate(
        avg_rating    = Avg('reviews__score'),
        reviews_count = Count('reviews', distinct=True),
    )
    if genre:
        games = games.filter(genre=genre)
    allowed = ['avg_rating', '-avg_rating', 'price', '-price', 'created_at', '-created_at', 'title']
    if sort not in allowed:
        sort = '-created_at'
    games = games.order_by(sort)
    top_users = User.objects.annotate(
        total_points=Sum('achievements__achievement__points')
    ).filter(total_points__gt=0).order_by('-total_points')[:5]
    recent_achievements = []
    if request.user.is_authenticated:
        recent_achievements = UserAchievement.objects.filter(
            user=request.user
        ).select_related('achievement__game').order_by('-unlocked_at')[:3]
    return render(request, 'catalog/index.html', {
        'games':               games,
        'genre':               genre,
        'sort':                sort,
        'genres':              Game.GENRE_CHOICES,
        'featured':            games.first(),
        'recent_achievements': recent_achievements,
        'top_users':           top_users,
    })


def search_view(request):
    q = request.GET.get('q', '').strip()
    games = []
    if q:
        games = Game.objects.filter(status='published').filter(
            Q(title__icontains=q) | Q(developer__icontains=q) | Q(genre__icontains=q)
        ).annotate(avg_rating=Avg('reviews__score'))[:10]
    if request.headers.get('HX-Request'):
        return render(request, 'catalog/partials/search_results.html', {'games': games, 'q': q})
    return redirect('index')


def game_detail(request, pk):
    game = get_object_or_404(
        Game.objects.annotate(
            avg_rating    = Avg('reviews__score'),
            reviews_count = Count('reviews', distinct=True),
        ), pk=pk
    )
    reviews      = game.reviews.select_related('user').all()
    achievements = game.achievements.all()
    screenshots  = game.screenshots.all()
    user_review   = None
    has_purchased = False
    user_ach_ids  = []
    if request.user.is_authenticated:
        user_review   = reviews.filter(user=request.user).first()
        has_purchased = Purchase.objects.filter(user=request.user, game=game).exists()
        user_ach_ids  = list(
            UserAchievement.objects.filter(
                user=request.user, achievement__game=game
            ).values_list('achievement_id', flat=True)
        )
    is_admin = request.user.is_authenticated and request.user.is_admin()
    is_dev   = request.user.is_authenticated and (request.user.is_developer() or is_admin)
    return render(request, 'catalog/game_detail.html', {
        'game':             game,
        'reviews':          reviews,
        'achievements':     achievements,
        'screenshots':      screenshots,
        'user_review':      user_review,
        'has_purchased':    has_purchased,
        'review_form':      ReviewForm(),
        'screenshot_form':  ScreenshotForm() if is_admin else None,
        'achievement_form': AchievementForm() if is_dev else None,
        'user_ach_ids':     user_ach_ids,
    })


# ── CRUD игр (admin) ──────────────────────────────────────────────────────────

@admin_required
def game_create(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        game = form.save()
        return redirect('game_detail', pk=game.pk)
    return render(request, 'catalog/game_form.html', {'form': form, 'action': 'Добавить игру'})


@admin_required
def game_update(request, pk):
    game = get_object_or_404(Game, pk=pk)
    form = GameForm(request.POST or None, request.FILES or None, instance=game)
    if form.is_valid():
        form.save()
        return redirect('game_detail', pk=pk)
    return render(request, 'catalog/game_form.html', {'form': form, 'action': 'Редактировать', 'game': game})


@admin_required
def game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        for ss in game.screenshots.all():
            ss.image.delete(save=False)
        if game.file:
            game.file.delete(save=False)
        if game.cover:
            game.cover.delete(save=False)
        game.delete()
        return redirect('index')
    return render(request, 'catalog/game_confirm_delete.html', {'game': game})


# ── Скриншоты ─────────────────────────────────────────────────────────────────

@developer_required
def screenshot_add(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        form = ScreenshotForm(request.POST, request.FILES)
        if form.is_valid():
            ss = form.save(commit=False)
            ss.game = game
            ss.save()
    # Редирект обратно — в студию если разработчик, на страницу игры если админ
    if request.user.is_developer() and not request.user.is_admin():
        return redirect('studio_analytics', pk=pk)
    return redirect('game_detail', pk=pk)


@developer_required
def screenshot_delete(request, pk):
    ss = get_object_or_404(Screenshot, pk=pk)
    game_pk = ss.game.pk
    if request.method == 'POST':
        ss.image.delete(save=False)
        ss.delete()
    if request.user.is_developer() and not request.user.is_admin():
        return redirect('studio_analytics', pk=game_pk)
    return redirect('game_detail', pk=game_pk)


# ── Достижения ────────────────────────────────────────────────────────────────

@developer_required
def achievement_create(request, game_pk):
    game = get_object_or_404(Game, pk=game_pk)
    # Разработчик может создавать только для своих игр
    if not request.user.is_admin() and game.developer_user != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        form = AchievementForm(request.POST, request.FILES)
        if form.is_valid():
            ach = form.save(commit=False)
            ach.game = game
            ach.save()
    if request.user.is_developer() and not request.user.is_admin():
        return redirect('studio_analytics', pk=game_pk)
    return redirect('game_detail', pk=game_pk)


@developer_required
def achievement_delete(request, pk):
    ach = get_object_or_404(Achievement, pk=pk)
    game_pk = ach.game.pk
    if not request.user.is_admin() and ach.game.developer_user != request.user:
        raise PermissionDenied
    if request.method == 'POST':
        ach.delete()
    if request.user.is_developer() and not request.user.is_admin():
        return redirect('studio_analytics', pk=game_pk)
    return redirect('game_detail', pk=game_pk)


# ── Покупка и скачивание ──────────────────────────────────────────────────────

@login_required
def buy_game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        _, created = Purchase.objects.get_or_create(
            user=request.user, game=game,
            defaults={'price_paid': game.price}
        )
        if created:
            check_and_unlock(request.user, 'buy_game', game=game)
    return redirect('game_detail', pk=pk)


@login_required
def game_download(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if not game.file:
        return redirect('game_detail', pk=pk)
    has_purchase = Purchase.objects.filter(user=request.user, game=game).exists()
    if not has_purchase and not request.user.is_admin():
        raise PermissionDenied
    return FileResponse(game.file.open('rb'), as_attachment=True, filename=f'{game.title}.zip')


# ── Отзывы ────────────────────────────────────────────────────────────────────

@login_required
def add_review(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        if not Review.objects.filter(user=request.user, game=game).exists():
            form = ReviewForm(request.POST)
            if form.is_valid():
                review      = form.save(commit=False)
                review.user = request.user
                review.game = game
                review.save()
                check_and_unlock(request.user, 'write_review', game=game)
    return redirect('game_detail', pk=pk)


@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.user == request.user or request.user.is_admin():
        game_pk = review.game.pk
        review.delete()
        if request.GET.get('next') == 'moderation':
            return redirect('moderation')
        return redirect('game_detail', pk=game_pk)
    raise PermissionDenied


# ── Библиотека ────────────────────────────────────────────────────────────────

@login_required
def library(request):
    purchases = Purchase.objects.filter(
        user=request.user).select_related('game').order_by('-purchased_at')
    return render(request, 'catalog/library.html', {'purchases': purchases})


# ── Аутентификация ────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('index')
    return render(request, 'catalog/register.html', {'form': form})


# ── Профиль ───────────────────────────────────────────────────────────────────

def profile_view(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    library_qs   = Purchase.objects.filter(user=profile_user).select_related('game')
    achievements = UserAchievement.objects.filter(user=profile_user).select_related('achievement__game')
    friends      = Friendship.get_friends(profile_user)
    friendship        = None
    friendship_status = None
    pending_requests  = []
    if request.user.is_authenticated:
        if request.user != profile_user:
            friendship = Friendship.objects.filter(
                Q(from_user=request.user, to_user=profile_user) |
                Q(from_user=profile_user, to_user=request.user)
            ).first()
            friendship_status = friendship.status if friendship else None
        else:
            pending_requests = Friendship.objects.filter(
                to_user=request.user, status='pending').select_related('from_user')
    total_points = achievements.aggregate(s=Sum('achievement__points'))['s'] or 0
    return render(request, 'catalog/profile.html', {
        'profile_user':      profile_user,
        'library':           library_qs,
        'achievements':      achievements,
        'friends':           friends,
        'friendship':        friendship,
        'friendship_status': friendship_status,
        'pending_requests':  pending_requests,
        'total_points':      total_points,
    })


@login_required
def profile_edit(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('profile', pk=request.user.pk)
    return render(request, 'catalog/profile_edit.html', {'form': form})


# ── Социальный модуль ─────────────────────────────────────────────────────────

@login_required
def friend_request(request, user_id):
    to_user = get_object_or_404(User, pk=user_id)
    if to_user != request.user:
        Friendship.objects.get_or_create(
            from_user=request.user, to_user=to_user, defaults={'status': 'pending'})
    return redirect('profile', pk=user_id)


@login_required
def friend_respond(request, friendship_id, action):
    friendship = get_object_or_404(Friendship, pk=friendship_id, to_user=request.user)
    if action == 'accept':
        friendship.status = 'accepted'
        friendship.save()
        check_and_unlock(request.user, 'add_friend')
        check_and_unlock(friendship.from_user, 'add_friend')
    elif action == 'decline':
        friendship.status = 'declined'
        friendship.save()
    return redirect('profile', pk=request.user.pk)


@login_required
def friend_remove(request, user_id):
    other = get_object_or_404(User, pk=user_id)
    Friendship.objects.filter(
        Q(from_user=request.user, to_user=other) |
        Q(from_user=other, to_user=request.user)
    ).delete()
    return redirect('profile', pk=request.user.pk)


# ── Сообщество ────────────────────────────────────────────────────────────────

def community(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.annotate(
        games_count=Count('purchases', distinct=True),
        ach_count=Count('achievements', distinct=True),
        total_pts=Sum('achievements__achievement__points'),
    ).order_by('-date_joined')
    if q:
        users = users.filter(username__icontains=q)
    friends_pks = set()
    pending_pks = set()
    incoming_pks = set()
    if request.user.is_authenticated:
        for f in Friendship.objects.filter(Q(from_user=request.user) | Q(to_user=request.user)):
            other = f.to_user if f.from_user == request.user else f.from_user
            if f.status == 'accepted':
                friends_pks.add(other.pk)
            elif f.status == 'pending' and f.from_user == request.user:
                pending_pks.add(other.pk)
            elif f.status == 'pending' and f.to_user == request.user:
                incoming_pks.add(other.pk)
    return render(request, 'catalog/community.html', {
        'users': users, 'q': q,
        'friends_pks': friends_pks, 'pending_pks': pending_pks, 'incoming_pks': incoming_pks,
    })


# ── Панель администратора ─────────────────────────────────────────────────────

@admin_required
def dashboard(request):
    games = Game.objects.annotate(avg_r=Avg('reviews__score'), rev_count=Count('reviews')).order_by('-created_at')
    return render(request, 'catalog/dashboard.html', {
        'games_count':     Game.objects.count(),
        'users_count':     User.objects.count(),
        'reviews_count':   Review.objects.count(),
        'purchases_count': Purchase.objects.count(),
        'recent_reviews':  Review.objects.select_related('user', 'game').order_by('-created_at')[:5],
        'games':           games,
    })


@admin_required
def dashboard_users(request):
    users = User.objects.annotate(
        games_count=Count('purchases', distinct=True),
        ach_count=Count('achievements', distinct=True),
    ).order_by('-date_joined')
    return render(request, 'catalog/dashboard_users.html', {'users': users})


@admin_required
def dashboard_achievements(request):
    achievements = Achievement.objects.select_related('game').annotate(
        unlocked_count=Count('userachievement')).order_by('game__title')
    return render(request, 'catalog/dashboard_achievements.html', {
        'achievements': achievements,
        'games': Game.objects.all(),
        'achievement_form': AchievementForm(),
    })


@admin_required
def dashboard_purchases(request):
    purchases = Purchase.objects.select_related('user', 'game').order_by('-purchased_at')
    return render(request, 'catalog/dashboard_purchases.html', {'purchases': purchases})


@admin_required
def moderation(request):
    reviews = Review.objects.select_related('user', 'game').order_by('-created_at')
    return render(request, 'catalog/moderation.html', {'reviews': reviews})


@admin_required
def game_moderation(request):
    pending_games = Game.objects.filter(status='pending').select_related('developer_user').order_by('created_at')
    return render(request, 'catalog/game_moderation.html', {'pending_games': pending_games})


@admin_required
def game_approve(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        game.status = 'published'
        game.rejection_reason = ''
        game.save()
    return redirect('game_moderation')


@admin_required
def game_reject(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == 'POST':
        game.status = 'rejected'
        game.rejection_reason = request.POST.get('reason', '').strip()
        game.save()
    return redirect('game_moderation')


# ── Панель разработчика ───────────────────────────────────────────────────────

@developer_required
def studio(request):
    games = Game.objects.filter(developer_user=request.user).annotate(
        avg_r=Avg('reviews__score'),
        rev_count=Count('reviews', distinct=True),
        purchases_count=Count('purchases', distinct=True),
    ).order_by('-created_at')
    stats = {
        'total':     games.count(),
        'published': games.filter(status='published').count(),
        'pending':   games.filter(status='pending').count(),
        'rejected':  games.filter(status='rejected').count(),
        'draft':     games.filter(status='draft').count(),
    }
    return render(request, 'catalog/studio.html', {'games': games, 'stats': stats})


@developer_required
def studio_game_create(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        game = form.save(commit=False)
        game.developer_user = request.user
        game.status = 'pending'
        game.save()
        return redirect('studio')
    return render(request, 'catalog/game_form.html', {'form': form, 'action': 'Добавить игру', 'studio': True})


@developer_required
def studio_game_update(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.developer_user != request.user and not request.user.is_admin():
        raise PermissionDenied
    form = GameForm(request.POST or None, request.FILES or None, instance=game)
    if form.is_valid():
        g = form.save(commit=False)
        if request.user.is_developer() and not request.user.is_admin():
            g.status = 'pending'
        g.save()
        return redirect('studio')
    return render(request, 'catalog/game_form.html', {'form': form, 'action': 'Редактировать', 'game': game, 'studio': True})


@developer_required
def studio_game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.developer_user != request.user and not request.user.is_admin():
        raise PermissionDenied
    if request.method == 'POST':
        game.delete()
        return redirect('studio')
    return render(request, 'catalog/game_confirm_delete.html', {'game': game, 'studio': True})


@developer_required
def studio_game_publish(request, pk):
    game = get_object_or_404(Game, pk=pk, developer_user=request.user)
    if request.method == 'POST':
        game.status = 'pending'
        game.rejection_reason = ''
        game.save()
    return redirect('studio')


@developer_required
def studio_analytics(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if game.developer_user != request.user and not request.user.is_admin():
        raise PermissionDenied
    from django.db.models.functions import TruncDay
    from datetime import timedelta
    from django.utils import timezone
    since = timezone.now() - timedelta(days=30)
    purchases_by_day = (
        Purchase.objects.filter(game=game, purchased_at__gte=since)
        .annotate(day=TruncDay('purchased_at')).values('day')
        .annotate(count=Count('id')).order_by('day')
    )
    reviews     = game.reviews.select_related('user').order_by('-created_at')
    screenshots = game.screenshots.all()
    achievements = game.achievements.annotate(unlocked_count=Count('userachievement'))
    return render(request, 'catalog/studio_analytics.html', {
        'game':             game,
        'purchases_by_day': list(purchases_by_day),
        'reviews':          reviews,
        'screenshots':      screenshots,
        'achievements':     achievements,
        'screenshot_form':  ScreenshotForm(),
        'achievement_form': AchievementForm(),
        'total_purchases':  game.purchases.count(),
        'total_revenue':    sum(p.price_paid for p in game.purchases.all()),
    })


# ── Публичная страница разработчика ───────────────────────────────────────────

def developer_page(request, username):
    dev = get_object_or_404(User, username=username)
    if not dev.is_developer() and not dev.is_admin():
        raise PermissionDenied
    games = Game.objects.filter(developer_user=dev, status='published').annotate(
        avg_r=Avg('reviews__score'),
        rev_count=Count('reviews', distinct=True),
        purchases_count=Count('purchases', distinct=True),
    )
    total_purchases = sum(g.purchases_count for g in games)
    total_reviews   = sum(g.rev_count for g in games)
    return render(request, 'catalog/developer_page.html', {
        'dev': dev, 'games': games,
        'total_purchases': total_purchases, 'total_reviews': total_reviews,
    })
