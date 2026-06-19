from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Avg, Sum, Q


class User(AbstractUser):
    ROLE_CHOICES = [
        ('player',    'Игрок'),
        ('developer', 'Разработчик'),
        ('admin',     'Администратор'),
    ]
    role   = models.CharField(max_length=10, choices=ROLE_CHOICES, default='player')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio    = models.TextField(blank=True, default='')

    def is_admin(self):
        return self.role == 'admin' or self.is_staff

    def is_developer(self):
        return self.role == 'developer'

    def is_player(self):
        return self.role == 'player'

    def total_points(self):
        result = self.achievements.aggregate(s=Sum('achievement__points'))
        return result['s'] or 0

    def __str__(self):
        return self.username


class Game(models.Model):
    GENRE_CHOICES = [
        ('rpg',       'RPG'),
        ('action',    'Экшен'),
        ('indie',     'Инди'),
        ('strategy',  'Стратегия'),
        ('simulator', 'Симулятор'),
        ('horror',    'Хоррор'),
        ('adventure', 'Приключения'),
        ('other',     'Другое'),
    ]
    STATUS_CHOICES = [
        ('draft',     'Черновик'),
        ('pending',   'На модерации'),
        ('published', 'Опубликована'),
        ('rejected',  'Отклонена'),
    ]
    title        = models.CharField(max_length=255, verbose_name='Название')
    description  = models.TextField(verbose_name='Описание')
    price        = models.DecimalField(max_digits=10, decimal_places=2,
                                       default=0, verbose_name='Цена (₽)')
    cover        = models.ImageField(upload_to='covers/', verbose_name='Обложка')
    developer    = models.CharField(max_length=200, verbose_name='Разработчик')
    genre        = models.CharField(max_length=20, choices=GENRE_CHOICES,
                                    default='other', verbose_name='Жанр')
    release_date = models.DateField(null=True, blank=True, verbose_name='Дата выпуска')
    file         = models.FileField(upload_to='distributives/', null=True, blank=True,
                                    verbose_name='Дистрибутив')
    created_at        = models.DateTimeField(auto_now_add=True)
    developer_user    = models.ForeignKey(
                            'User',
                            on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='developed_games',
                            verbose_name='Разработчик (пользователь)')
    status            = models.CharField(
                            max_length=10,
                            choices=STATUS_CHOICES,
                            default='published',
                            verbose_name='Статус')
    rejection_reason  = models.TextField(
                            blank=True, default='',
                            verbose_name='Причина отклонения')

    class Meta:
        verbose_name        = 'Игра'
        verbose_name_plural = 'Игры'
        ordering            = ['-created_at']

    def __str__(self):
        return self.title

    def avg_rating(self):
        result = self.reviews.aggregate(avg=Avg('score'))
        return round(result['avg'] or 0, 1)

    def reviews_count(self):
        return self.reviews.count()

    def get_genre_display_ru(self):
        return dict(self.GENRE_CHOICES).get(self.genre, self.genre)


class Screenshot(models.Model):
    game    = models.ForeignKey(Game, on_delete=models.CASCADE,
                                related_name='screenshots')
    image   = models.ImageField(upload_to='screenshots/')
    caption = models.CharField(max_length=300, blank=True)

    class Meta:
        verbose_name        = 'Скриншот'
        verbose_name_plural = 'Скриншоты'


class Achievement(models.Model):
    TRIGGER_CHOICES = [
        ('buy_game',     'Купить эту игру'),
        ('write_review', 'Написать отзыв на эту игру'),
        ('buy_any_3',    'Купить любые 3 игры'),
        ('buy_any_5',    'Купить любые 5 игр'),
        ('buy_any_10',   'Купить любые 10 игр'),
        ('write_any_3',  'Написать 3 отзыва'),
        ('write_any_5',  'Написать 5 отзывов'),
        ('add_friend',   'Добавить первого друга'),
        ('manual',       'Вручную (через панель)'),
    ]

    game        = models.ForeignKey(Game, on_delete=models.CASCADE,
                                    related_name='achievements')
    name        = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание условия')
    icon        = models.ImageField(upload_to='achievements/', null=True, blank=True)
    points      = models.PositiveIntegerField(default=10, verbose_name='Очки')
    trigger     = models.CharField(
                      max_length=20,
                      choices=TRIGGER_CHOICES,
                      default='manual',
                      verbose_name='Условие выдачи')

    class Meta:
        verbose_name        = 'Достижение'
        verbose_name_plural = 'Достижения'

    def __str__(self):
        return f'{self.game.title} — {self.name}'


class UserAchievement(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ('user', 'achievement')
        verbose_name        = 'Достижение пользователя'
        verbose_name_plural = 'Достижения пользователей'


class Purchase(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='purchases')
    game         = models.ForeignKey(Game, on_delete=models.CASCADE,
                                     related_name='purchases')
    price_paid   = models.DecimalField(max_digits=10, decimal_places=2)
    purchased_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ('user', 'game')
        verbose_name        = 'Покупка'
        verbose_name_plural = 'Покупки'


class Review(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='reviews')
    game       = models.ForeignKey(Game, on_delete=models.CASCADE,
                                   related_name='reviews')
    score      = models.PositiveSmallIntegerField(
                     choices=[(i, f'{i} ★') for i in range(1, 6)])
    text       = models.TextField(verbose_name='Текст отзыва')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ('user', 'game')
        ordering            = ['-created_at']
        verbose_name        = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.user.username} → {self.game.title} ({self.score}★)'


class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Ожидание'),
        ('accepted', 'Принята'),
        ('declined', 'Отклонена'),
    ]
    from_user  = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='sent_requests')
    to_user    = models.ForeignKey(User, on_delete=models.CASCADE,
                                   related_name='received_requests')
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES,
                                  default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ('from_user', 'to_user')
        verbose_name        = 'Дружба'
        verbose_name_plural = 'Дружеские связи'

    @staticmethod
    def get_friends(user):
        sent     = Friendship.objects.filter(from_user=user, status='accepted')\
                                     .values_list('to_user', flat=True)
        received = Friendship.objects.filter(to_user=user, status='accepted')\
                                     .values_list('from_user', flat=True)
        return User.objects.filter(pk__in=list(sent) + list(received))


# ── Личные сообщения ──────────────────────────────────────────────────────────

class Conversation(models.Model):
    """Диалог между двумя пользователями."""
    participants = models.ManyToManyField(
                       User, related_name='conversations')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def get_other(self, user):
        return self.participants.exclude(pk=user.pk).first()

    def unread_count(self, user):
        return self.messages.filter(
            is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """Сообщение в диалоге."""
    conversation = models.ForeignKey(
                       Conversation, on_delete=models.CASCADE,
                       related_name='messages')
    sender       = models.ForeignKey(
                       User, on_delete=models.CASCADE,
                       related_name='sent_messages')
    text         = models.TextField()
    is_read      = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.text[:50]}'


# ── Форум ─────────────────────────────────────────────────────────────────────

class ForumCategory(models.Model):
    """Раздел форума."""
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=10, default='💬')
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name        = 'Раздел форума'
        verbose_name_plural = 'Разделы форума'

    def __str__(self):
        return self.name


class ForumThread(models.Model):
    """Тема на форуме."""
    category   = models.ForeignKey(
                     ForumCategory, on_delete=models.CASCADE,
                     related_name='threads')
    author     = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='threads')
    title      = models.CharField(max_length=300)
    is_pinned  = models.BooleanField(default=False)
    is_closed  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        verbose_name        = 'Тема форума'
        verbose_name_plural = 'Темы форума'

    def __str__(self):
        return self.title

    def post_count(self):
        return self.posts.count()

    def last_post(self):
        return self.posts.order_by('-created_at').first()


class ForumPost(models.Model):
    """Пост в теме форума."""
    thread     = models.ForeignKey(
                     ForumThread, on_delete=models.CASCADE,
                     related_name='posts')
    author     = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='forum_posts')
    text       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes      = models.ManyToManyField(
                     User, related_name='liked_posts', blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author.username} в {self.thread.title}'


# ── Уведомления ───────────────────────────────────────────────────────────────

class Notification(models.Model):
    """Уведомление пользователя."""
    TYPE_CHOICES = [
        ('message',       'Новое сообщение'),
        ('forum_reply',   'Ответ в теме'),
        ('friend_req',    'Заявка в друзья'),
        ('friend_accept', 'Заявка принята'),
        ('achievement',   'Новое достижение'),
        ('game_approved', 'Игра одобрена'),
        ('game_rejected', 'Игра отклонена'),
    ]
    recipient  = models.ForeignKey(
                     User, on_delete=models.CASCADE,
                     related_name='notifications')
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text       = models.CharField(max_length=300)
    link       = models.CharField(max_length=200, blank=True)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @staticmethod
    def create(recipient, ntype, text, link=''):
        if recipient:
            Notification.objects.create(
                recipient=recipient,
                type=ntype, text=text, link=link)
