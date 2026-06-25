from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

USERNAME_MAX_LENGTH = 150


class User(AbstractUser):
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        verbose_name='Имя пользователя',
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Электронная почта',
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        blank=True,
        null=True,
        default='',
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username

    def delete_avatar(self):
        if self.avatar:
            self.avatar.delete(save=False)
        self.avatar = None
        self.save(update_fields=('avatar',))
