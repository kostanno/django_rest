import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from .models import Course, Subscription

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_email(course_id, lesson_title):
    try:
        course = Course.objects.get(id=course_id)
        subscriptions = Subscription.objects.filter(
            course=course,
            is_active=True
        ).select_related('пользователь')

        if not subscriptions:
            logger.info(f"не активировали курс {course.title}")
            return

        subject = f'Новый урок в курсе "{course.title}"'

        for subscription in subscriptions:
            user = subscription.user
            html_message = render_to_string('lms/email/course_update.html', {
                'user': user,
                'course': course,
                'lesson_title': lesson_title,
            })

            plain_message = strip_tags(html_message)

            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
                logger.info(f"курс отправлен на: {user.email} ")
    except Exception as e:
        logger.error(f"{str(e)}")



@shared_task
def check_new_lessons_and_notify():
    try:
        pass
    except Exception as e:
        logger.error(f"Error in check_new_lessons_and_notify: {str(e)}")