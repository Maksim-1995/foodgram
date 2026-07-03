from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import Subscription, User


@admin.register(User)
class FoodgramUserAdmin(UserAdmin):
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
    )
    search_fields = ('email', 'username')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    ordering = ('id',)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created_at')
    search_fields = ('user__email', 'user__username', 'author__username')
    list_filter = ('created_at',)
