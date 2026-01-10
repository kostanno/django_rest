from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import Group
from django.urls import reverse

from .models import Course, Lesson, Subscription
from users.models import User


class LessonCRUDTestCase(APITestCase):
    """Тесты для CRUD операций с уроками."""

    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем пользователей
        self.user = User.objects.create(
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            is_staff=False,
            is_superuser=False
        )
        self.user.set_password('testpassword123')
        self.user.save()

        self.moderator = User.objects.create(
            email='moderator@example.com',
            first_name='Moderator',
            last_name='Test',
            is_staff=False,
            is_superuser=False
        )
        self.moderator.set_password('modpassword123')
        self.moderator.save()

        # Создаем группу модераторов и добавляем пользователя
        moderators_group, created = Group.objects.get_or_create(name='Модераторы')
        self.moderator.groups.add(moderators_group)

        self.admin = User.objects.create(
            email='admin@example.com',
            first_name='Admin',
            last_name='Test',
            is_staff=True,
            is_superuser=True
        )
        self.admin.set_password('adminpassword123')
        self.admin.save()

        # Создаем курс
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

        # Создаем урок
        self.lesson_data = {
            'title': 'Test Lesson',
            'description': 'Test Lesson Description',
            'video_link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'course': self.course.id
        }

        # Создаем клиенты для разных пользователей
        self.user_client = APIClient()
        self.moderator_client = APIClient()
        self.admin_client = APIClient()

        # Аутентифицируем клиентов
        self.user_client.force_authenticate(user=self.user)
        self.moderator_client.force_authenticate(user=self.moderator)
        self.admin_client.force_authenticate(user=self.admin)

    def test_create_lesson_authenticated_user(self):
        """Тест создания урока аутентифицированным пользователем."""
        url = reverse('lms:lesson-list')
        response = self.user_client.post(url, self.lesson_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 1)
        self.assertEqual(Lesson.objects.get().title, 'Test Lesson')
        self.assertEqual(Lesson.objects.get().owner, self.user)

    def test_create_lesson_moderator_forbidden(self):
        """Тест что модератор не может создавать уроки."""
        url = reverse('lms:lesson-list')
        response = self.moderator_client.post(url, self.lesson_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_create_lesson_unauthenticated(self):
        """Тест что неаутентифицированный пользователь не может создавать уроки."""
        client = APIClient()
        url = reverse('lms:lesson-list')
        response = client.post(url, self.lesson_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_lesson_invalid_youtube_link(self):
        """Тест создания урока с невалидной ссылкой (не YouTube)."""
        invalid_data = self.lesson_data.copy()
        invalid_data['video_link'] = 'https://vimeo.com/123456'

        url = reverse('lms:lesson-list')
        response = self.user_client.post(url, invalid_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('video_link', response.data)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_list_lessons_authenticated(self):
        """Тест получения списка уроков аутентифицированным пользователем."""
        # Создаем несколько уроков
        Lesson.objects.create(
            title='Lesson 1',
            description='Description 1',
            video_link='https://www.youtube.com/watch?v=test1',
            course=self.course,
            owner=self.user
        )
        Lesson.objects.create(
            title='Lesson 2',
            description='Description 2',
            video_link='https://youtu.be/test2',
            course=self.course,
            owner=self.moderator
        )

        url = reverse('lms:lesson-list')
        response = self.user_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Пользователь видит только свои уроки
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Lesson 1')

    def test_moderator_can_view_all_lessons(self):
        """Тест что модератор видит все уроки."""
        Lesson.objects.create(
            title='Lesson 1',
            description='Description 1',
            video_link='https://www.youtube.com/watch?v=test1',
            course=self.course,
            owner=self.user
        )
        Lesson.objects.create(
            title='Lesson 2',
            description='Description 2',
            video_link='https://youtu.be/test2',
            course=self.course,
            owner=self.moderator
        )

        url = reverse('lms:lesson-list')
        response = self.moderator_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Модератор видит все уроки
        self.assertEqual(len(response.data['results']), 2)

    def test_update_lesson_owner(self):
        """Тест обновления урока владельцем."""
        lesson = Lesson.objects.create(
            title='Original Lesson',
            description='Original Description',
            video_link='https://www.youtube.com/watch?v=original',
            course=self.course,
            owner=self.user
        )

        url = reverse('lms:lesson-update', args=[lesson.id])
        update_data = {
            'title': 'Updated Lesson',
            'description': 'Updated Description',
            'video_link': 'https://youtu.be/updated',
            'course': self.course.id
        }

        response = self.user_client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, 'Updated Lesson')

    def test_update_lesson_moderator(self):
        """Тест что модератор может обновлять любой урок."""
        lesson = Lesson.objects.create(
            title='Original Lesson',
            description='Original Description',
            video_link='https://www.youtube.com/watch?v=original',
            course=self.course,
            owner=self.user  # Урок принадлежит обычному пользователю
        )

        url = reverse('lms:lesson-update', args=[lesson.id])
        update_data = {
            'title': 'Updated by Moderator',
            'description': 'Updated Description',
            'video_link': 'https://youtu.be/updated',
            'course': self.course.id
        }

        response = self.moderator_client.put(url, update_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, 'Updated by Moderator')

    def test_delete_lesson_owner(self):
        """Тест удаления урока владельцем."""
        lesson = Lesson.objects.create(
            title='Lesson to Delete',
            description='Description',
            video_link='https://www.youtube.com/watch?v=delete',
            course=self.course,
            owner=self.user
        )

        url = reverse('lms:lesson-delete', args=[lesson.id])
        response = self.user_client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Lesson.objects.count(), 0)

    def test_delete_lesson_moderator_forbidden(self):
        """Тест что модератор не может удалять уроки."""
        lesson = Lesson.objects.create(
            title='Lesson to Delete',
            description='Description',
            video_link='https://www.youtube.com/watch?v=delete',
            course=self.course,
            owner=self.user
        )

        url = reverse('lms:lesson-delete', args=[lesson.id])
        response = self.moderator_client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 1)


class SubscriptionTestCase(APITestCase):
    """Тесты для функционала подписки на курсы."""

    def setUp(self):
        """Настройка тестовых данных."""
        self.user = User.objects.create(
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user.set_password('testpassword123')
        self.user.save()

        self.other_user = User.objects.create(
            email='otheruser@example.com',
            first_name='Other',
            last_name='User'
        )
        self.other_user.set_password('otherpassword123')
        self.other_user.save()

        # Создаем курсы
        self.course1 = Course.objects.create(
            title='Course 1',
            description='Description 1',
            owner=self.user
        )
        self.course2 = Course.objects.create(
            title='Course 2',
            description='Description 2',
            owner=self.other_user
        )

        # Создаем клиенты
        self.user_client = APIClient()
        self.other_client = APIClient()

        self.user_client.force_authenticate(user=self.user)
        self.other_client.force_authenticate(user=self.other_user)

    def test_subscribe_to_course(self):
        """Тест подписки на курс."""
        url = reverse('lms:course-subscribe', args=[self.course1.id])
        response = self.user_client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Subscription.objects.filter(
            user=self.user,
            course=self.course1,
            is_active=True
        ).exists())

    def test_subscribe_already_subscribed(self):
        """Тест повторной подписки на курс."""
        # Создаем подписку
        Subscription.objects.create(
            user=self.user,
            course=self.course1,
            is_active=True
        )

        url = reverse('lms:course-subscribe', args=[self.course1.id])
        response = self.user_client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Вы уже подписаны на этот курс')

    def test_unsubscribe_from_course(self):
        """Тест отписки от курса."""
        # Создаем подписку
        Subscription.objects.create(
            user=self.user,
            course=self.course1,
            is_active=True
        )

        url = reverse('lms:course-unsubscribe', args=[self.course1.id])
        response = self.user_client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subscription = Subscription.objects.get(user=self.user, course=self.course1)
        self.assertFalse(subscription.is_active)

    def test_unsubscribe_not_subscribed(self):
        """Тест отписки от курса, на который не подписан."""
        url = reverse('lms:course-unsubscribe', args=[self.course1.id])
        response = self.user_client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_course_list_shows_subscription_status(self):
        """Тест что список курсов показывает статус подписки."""
        # Пользователь подписан на course1
        Subscription.objects.create(
            user=self.user,
            course=self.course1,
            is_active=True
        )

        url = reverse('lms:course-list')
        response = self.user_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Находим course1 в результатах
        for course_data in response.data['results']:
            if course_data['id'] == self.course1.id:
                self.assertTrue(course_data['is_subscribed'])
                break
        else:
            self.fail("Course 1 not found in response")

    def test_course_detail_shows_subscription_status(self):
        """Тест что детальная информация о курсе показывает статус подписки."""
        # Пользователь подписан на course1
        Subscription.objects.create(
            user=self.user,
            course=self.course1,
            is_active=True
        )

        url = reverse('lms:course-detail', args=[self.course1.id])
        response = self.user_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_subscribed'])

    def test_list_user_subscriptions(self):
        """Тест получения списка подписок пользователя."""
        # Создаем несколько подписок
        Subscription.objects.create(user=self.user, course=self.course1, is_active=True)
        Subscription.objects.create(user=self.user, course=self.course2, is_active=True)
        Subscription.objects.create(user=self.other_user, course=self.course1, is_active=True)

        url = reverse('users:subscription-list')
        response = self.user_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Пользователь должен видеть только свои подписки
        self.assertEqual(len(response.data['results']), 2)


class PaginationTestCase(APITestCase):
    """Тесты пагинации."""

    def setUp(self):
        self.user = User.objects.create(
            email='testuser@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user.set_password('testpassword123')
        self.user.save()

        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            owner=self.user
        )

        # Создаем много уроков для тестирования пагинации
        for i in range(15):
            Lesson.objects.create(
                title=f'Lesson {i}',
                description=f'Description {i}',
                video_link=f'https://www.youtube.com/watch?v=test{i}',
                course=self.course,
                owner=self.user
            )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_lessons_pagination_default(self):
        """Тест пагинации уроков по умолчанию (10 на странице)."""
        url = reverse('lms:lesson-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 10)  # page_size по умолчанию
        self.assertIn('next', response.data)  # Должна быть следующая страница

    def test_lessons_pagination_custom_page_size(self):
        """Тест пагинации уроков с кастомным размером страницы."""
        url = reverse('lms:lesson-list') + '?page_size=5'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_courses_pagination(self):
        """Тест пагинации курсов."""
        # Создаем больше курсов
        for i in range(10):
            Course.objects.create(
                title=f'Course {i}',
                description=f'Description {i}',
                owner=self.user
            )

        url = reverse('lms:course-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # По умолчанию 5 курсов на странице
        self.assertEqual(len(response.data['results']), 5)