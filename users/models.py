from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import UserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(UserManager):
    """Кастомный менеджер для аутентификации"""

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Вы не ввели почту')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя"""

    username = None
    email = models.EmailField(_('Укажиете вашу почту'), unique=True)
    phone = models.CharField(_('Укажите ваш номер телефона'), max_length=20, blank=True)
    city = models.CharField(_('Укажите ваш город'), max_length=100, blank=True)
    avatar = models.ImageField(_('Загрузите свое фото.'), upload_to='avatars/', blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email
