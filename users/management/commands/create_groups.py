from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from lms.models import Course, Lesson


class Command(BaseCommand):
    help = 'Создает группу модераторов и назначает права'

    def handle(self, *args, **options):
        moderators_group, created = Group.objects.get_or_create(name='Модераторы')
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Модераторы" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Модераторы" уже существует'))
        course_content_type = ContentType.objects.get_for_model(Course)
        lesson_content_type = ContentType.objects.get_for_model(Lesson)
        view_course_permission = Permission.objects.get(codename='view_course', content_type=course_content_type)
        change_course_permission = Permission.objects.get(codename='change_course', content_type=course_content_type)
        view_lesson_permission = Permission.objects.get(codename='view_lesson', content_type=lesson_content_type)
        change_lesson_permission = Permission.objects.get(codename='change_lesson', content_type=lesson_content_type)
        moderators_group.permissions.add(
            view_course_permission,
            change_course_permission,
            view_lesson_permission,
            change_lesson_permission
        )

        self.stdout.write(self.style.SUCCESS('Права назначены группе "Модераторы"'))