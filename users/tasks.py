from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
import logging

from config import settings

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def block_inactive_users():

    try:
        one_month_ago = timezone.now() - timedelta(days=30)
        inactive_users = User.objects.filter(
            last_login__lt=one_month_ago,
            is_active=True
        ).exclude(
            is_superuser=True
        )

        count = inactive_users.count()

        if count > 0:
            inactive_users.update(is_active=False)
            logger.info(f"заблокировано {count} неактивных пользователей")
            blocked_emails = list(inactive_users.values_list('почта', flat=True))
            logger.info(f"заблокированные почтовые адреса: {blocked_emails}")

            return {
                'blocked_count': count,
                'blocked_emails': blocked_emails,
                'timestamp': timezone.now().isoformat()
            }
        else:
            logger.info("No inactive users to block")
            return {'blocked_count': 0, 'message': 'No inactive users found'}

    except Exception as e:
        logger.error(f"Error in block_inactive_users task: {str(e)}")
        raise


@shared_task
def send_welcome_email(user_id):
    try:
        user = User.objects.get(id=user_id)

        subject = 'Добро пожаловать в нашу образовательную платформу!'
        message = f'''
        Здравствуйте, {user.first_name}!
        Добро пожаловать в нашу образовательную платформу!
        Ваш аккаунт успешно создан.
        Email: {user.email}
        Начните изучение курсов прямо сейчас!
        '''

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        logger.info(f"добро пожаловать  {user.email}")

    except User.DoesNotExist:
        logger.error(f"User with id {user_id}")
    except Exception as e:
        logger.error(f" {str(e)}")