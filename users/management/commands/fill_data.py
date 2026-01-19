from django.core.management.base import BaseCommand
from users.models import User, Payment
from lms.models import Course, Lesson
from datetime import datetime, timedelta
import random


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(
            email='testuser@example.com',
            defaults={
                'first_name': 'Тестовый',
                'last_name': 'Пользователь',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            user.set_password('testpassword123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Создан тестовый пользователь: {user.email}'))

        courses = list(Course.objects.all())
        lessons = list(Lesson.objects.all())

        if not courses and not lessons:
            self.stdout.write(
                self.style.ERROR('Нет курсов и уроков для создания платежей. Создайте сначала курсы и уроки.'))
            return

        payments_data = []

        for i, course in enumerate(courses[:3]):  # Берем первые 3 курса
            payment_date = datetime.now() - timedelta(days=random.randint(1, 30))

            payment = Payment(
                user=user,
                payment_date=payment_date,
                paid_course=course,
                paid_lesson=None,
                amount=random.randint(1000, 10000),
                payment_method=random.choice([Payment.CASH, Payment.TRANSFER])
            )
            payments_data.append(payment)

        # Платежи за уроки
        for i, lesson in enumerate(lessons[:3]):  # Берем первые 3 урока
            payment_date = datetime.now() - timedelta(days=random.randint(1, 30))

            payment = Payment(
                user=user,
                payment_date=payment_date,
                paid_course=None,
                paid_lesson=lesson,
                amount=random.randint(100, 2000),
                payment_method=random.choice([Payment.CASH, Payment.TRANSFER])
            )
            payments_data.append(payment)

        # Сохраняем все платежи
        Payment.objects.bulk_create(payments_data)

        self.stdout.write(self.style.SUCCESS(f'Создано {len(payments_data)} тестовых платежей'))