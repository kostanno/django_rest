from django.conf import settings
from django.db import models


class Course(models.Model):
    """Модель курса."""
    title = models.CharField(max_length=255, verbose_name='Название')
    preview = models.ImageField(upload_to='courses/previews/',
                                verbose_name='Превью',
                                blank=True,
                                null=True)
    description = models.TextField(verbose_name='Описание', blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.SET_NULL,
                              null=True,
                              blank=True,
                              verbose_name='Владелец',
                              related_name='courses_owned')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    preview = models.ImageField(upload_to='lessons/previews/',
                                verbose_name='Превью',
                                blank=True,
                                null=True)
    video_link = models.URLField(verbose_name='Ссылка на видео')
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE,
                               related_name='lessons',
                               verbose_name='Курс')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.SET_NULL,
                              null=True,
                              blank=True,
                              verbose_name='Владелец',
                              related_name='lessons_owned')

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return f"{self.title} (Курс: {self.course.title})"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Курс'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подписки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} подписан на {self.course.title}"