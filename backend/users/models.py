from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


REGEX_SIGNS = RegexValidator(r'^[\w.@+-]+\Z', 'Поддерживаемые символы.')
REGEX_ME = RegexValidator(r'^(?!me$).*$', 'Имя пользователя не может быть "me".')


class User(AbstractUser):
    """Модель пользователей."""
    username = models.CharField(
        unique=True,
        max_length=150,
        validators=(REGEX_SIGNS, REGEX_ME),
        verbose_name='Никнейм пользователя',
        help_text='Укажите никнейм пользователя'
    )
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='E-mail пользователя',
        help_text='Укажите e-mail пользователя'
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя пользователя',
        help_text='Укажите имя пользователя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия пользователя',
        help_text='Укажите фамилия пользователя'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']
    USERNAME_FIELD = 'email'

    class Meta:
        ordering = ('id',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions'  # Подписки пользователя
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers'  # Подписчики пользователя
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_following'
            )
        ]
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
