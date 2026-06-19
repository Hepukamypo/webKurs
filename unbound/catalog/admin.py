from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (User, Game, Screenshot, Achievement, UserAchievement,
                   Purchase, Review, Friendship,
                   ForumCategory, ForumThread, ForumPost, Notification)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'role', 'date_joined')
    list_filter   = ('role', 'is_staff')
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('Профиль', {'fields': ('role', 'avatar', 'bio')}),
    )


class ScreenshotInline(admin.TabularInline):
    model = Screenshot
    extra = 1


class AchievementInline(admin.TabularInline):
    model = Achievement
    extra = 1


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display  = ('title', 'developer', 'genre', 'price', 'created_at')
    list_filter   = ('genre',)
    search_fields = ('title', 'developer')
    inlines       = [ScreenshotInline, AchievementInline]


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'game', 'points')
    list_filter  = ('game',)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'price_paid', 'purchased_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('user', 'game', 'score', 'created_at')
    list_filter   = ('score',)
    search_fields = ('user__username', 'game__title')


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'status', 'created_at')
    list_filter  = ('status',)


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'order')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_pinned', 'is_closed', 'created_at')
    list_filter  = ('category', 'is_pinned', 'is_closed')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'type', 'text', 'is_read', 'created_at')
    list_filter  = ('type', 'is_read')
