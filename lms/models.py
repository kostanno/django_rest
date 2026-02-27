from django.conf import settings
from django.db import models
from lms.services import StripeService


class Course(models.Model):
    """Модель курса с поддержкой Stripe."""

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание', blank=True)
    preview = models.ImageField(
        upload_to='courses/previews/',
        verbose_name='Превью',
        blank=True,
        null=True
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Владелец',
        related_name='courses_owned'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='Цена курса'
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='Платный курс'
    )

    # Поля для Stripe
    stripe_product_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Stripe Product ID'
    )
    stripe_price_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Stripe Price ID'
    )

    # Дополнительные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Автоматическое создание/обновление продукта в Stripe при сохранении."""

        # Проверяем, является ли курс платным
        if self.price > 0 and not self.is_paid:
            self.is_paid = True

        # Если курс платный и у него нет Stripe ID, создаем продукт и цену
        if self.is_paid and self.price > 0:
            try:
                # Если нет продукта, создаем его
                if not self.stripe_product_id:
                    product = StripeService.create_product(self)
                    self.stripe_product_id = product.id

                # Если нет цены или цена изменилась, создаем новую
                if not self.stripe_price_id:
                    price = StripeService.create_price(self.stripe_product_id, self.price)
                    self.stripe_price_id = price.id
            except Exception as e:
                # Логируем ошибку, но не прерываем сохранение
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка при работе со Stripe: {str(e)}")

        super().save(*args, **kwargs)

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