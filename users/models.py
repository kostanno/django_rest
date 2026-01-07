from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Кастомная модель пользователя с авторизацией"""

    username = None
    email = models.EmailField(_('ваша почта'), unique=True)
    phone = models.CharField(_('номер телефона'), max_length=20, blank=True)
    city = models.CharField(_('город'), max_length=100, blank=True)
    avatar = models.ImageField(_('ваше фото'), upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


class Payment(models.Model):
    """Модель платежей."""

    CASH = 'cash'
    TRANSFER = 'transfer'

    PAYMENT_METHOD_CHOICES = [
        (CASH, 'Наличные'),
        (TRANSFER, 'Перевод на счет'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Пользователь'
    )

    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата оплаты'
    )

    paid_course = models.ForeignKey(
        'lms.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Оплаченный курс'
    )
    paid_lesson = models.ForeignKey(
        'lms.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Оплаченный урок'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма оплаты'
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Способ оплаты'
    )

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-payment_date']

    def __str__(self):
        if self.paid_course:
            return f"Платеж {self.amount} от {self.user.email} за курс: {self.paid_course.title}"
        elif self.paid_lesson:
            return f"Платеж {self.amount} от {self.user.email} за урок: {self.paid_lesson.title}"
        else:
            return f"Платеж {self.amount} от {self.user.email}"

    def clean(self):
        """Проверка, что указан либо курс, либо урок, но не оба одновременно."""
        from django.core.exceptions import ValidationError
        if self.paid_course and self.paid_lesson:
            raise ValidationError('Можно указать только курс или только урок, но не оба одновременно.')
        if not self.paid_course and not self.paid_lesson:
            raise ValidationError('Необходимо указать либо курс, либо урок.')