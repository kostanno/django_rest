from django.conf import settings
from django.db import models


class Course(models.Model):
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
                              related_name='courses')


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
                              related_name='lessons')

