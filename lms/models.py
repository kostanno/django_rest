from django.db import models


class Course(models.Model):
    """Модель курса"""
    title = models.CharField(max_length=255, verbose_name='Название')
    preview = models.ImageField(upload_to='courses/previews/',
                                verbose_name='Превью',
                                blank=True,
                                null=True)
    description = models.TextField(verbose_name='Описание', blank=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока"""
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

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'

    def __str__(self):
        return f"{self.title} (Курс: {self.course.title})"