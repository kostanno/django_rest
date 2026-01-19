import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {

    'block-inactive-users-daily-3am': {
        'task': 'users.tasks.block_inactive_users',
        'schedule': crontab(hour=3, minute=0),
        'args': (),
        'options': {
            'queue': 'periodic_tasks',
            'priority': 5,
        }
    },


    'block-inactive-users-daily-2pm': {
        'task': 'users.tasks.block_inactive_users',
        'schedule': crontab(hour=14, minute=0),
        'args': (),
        'options': {
            'queue': 'periodic_tasks',
            'priority': 3,
        }
    },

    'check-new-lessons-every-30min': {
        'task': 'lms.tasks.check_new_lessons_and_notify',
        'schedule': crontab(minute='*/30'),
        'args': (),
        'options': {
            'queue': 'periodic_tasks',
            'priority': 4,
        }
    },

    'clean-celery-results-weekly': {
        'task': 'config.tasks.clean_celery_results',
        'schedule': crontab(hour=1, minute=0, day_of_week='sunday'),
        'args': (),
        'options': {
            'queue': 'maintenance',
            'priority': 2,
        }
    },

    'send-user-statistics-monthly': {
        'task': 'users.tasks.send_user_statistics',
        'schedule': crontab(hour=2, minute=0, day_of_month='1'),
        'args': (),
        'options': {
            'queue': 'reports',
            'priority': 1,
        }
    },
}

app.conf.timezone = settings.CELERY_TIMEZONE


app.conf.task_queues = {
    'default': {
        'exchange': 'default',
        'exchange_type': 'direct',
        'routing_key': 'default',
    },
    'periodic_tasks': {
        'exchange': 'periodic_tasks',
        'exchange_type': 'direct',
        'routing_key': 'periodic_tasks',
    },
    'emails': {
        'exchange': 'emails',
        'exchange_type': 'direct',
        'routing_key': 'emails',
    },
    'reports': {
        'exchange': 'reports',
        'exchange_type': 'direct',
        'routing_key': 'reports',
    },
    'maintenance': {
        'exchange': 'maintenance',
        'exchange_type': 'direct',
        'routing_key': 'maintenance',
    },
}


app.conf.task_routes = {
    'users.tasks.block_inactive_users': {'queue': 'periodic_tasks'},
    'users.tasks.send_welcome_email': {'queue': 'emails'},
    'users.tasks.send_user_statistics': {'queue': 'reports'},
    'lms.tasks.send_course_update_email': {'queue': 'emails'},
    'lms.tasks.check_new_lessons_and_notify': {'queue': 'periodic_tasks'},
    'config.tasks.clean_celery_results': {'queue': 'maintenance'},
}

app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 1000
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60
app.conf.task_soft_time_limit = 25 * 60