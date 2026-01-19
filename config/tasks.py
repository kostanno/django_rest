from celery import shared_task
from django_celery_results.models import TaskResult
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def clean_celery_results():
    """
    Очищает старые результаты задач Celery (старше 7 дней).
    """
    try:
        seven_days_ago = timezone.now() - timedelta(days=7)

        deleted_count, _ = TaskResult.objects.filter(
            date_done__lt=seven_days_ago
        ).delete()

        logger.info(f"Cleaned up {deleted_count} old celery results")

        return {
            'deleted_count': deleted_count,
            'timestamp': timezone.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error cleaning celery results: {str(e)}")
        raise