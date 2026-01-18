from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, generics, status, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
import stripe

from .models import Course, Lesson, Subscription
from .paginators import LessonPagination
from .permissions import IsModerator
from .serializers import (
    CourseSerializer,
    LessonSerializer,
    SubscriptionSerializer,
    CoursePaymentSerializer,
    StripeCheckoutSerializer,
    PaymentStatusSerializer
)
from lms.services import StripeService
from users.models import Payment


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для CRUD операций с курсами."""

    @swagger_auto_schema(
        operation_summary="Получить список курсов",
        operation_description="Возвращает список курсов с пагинацией",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Номер страницы", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Размер страницы", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: CourseSerializer(many=True),
            401: "Не авторизован",
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Создать курс",
        operation_description="Создание нового курса. Доступно только для авторизованных пользователей, не являющихся модераторами.",
        request_body=CourseSerializer,
        responses={
            201: CourseSerializer,
            400: "Ошибка валидации",
            401: "Не авторизован",
            403: "Нет прав для создания курса",
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        method='post',
        operation_summary="Подписаться на курс",
        operation_description="""
        Подписка на обновления курса.

        Пользователь будет получать уведомления о новых уроках в этом курсе.
        Одна подписка на курс для пользователя.
        """,
        responses={
            201: openapi.Response(
                description="Подписка создана",
                examples={
                    'application/json': {
                        'detail': 'Вы подписались на курс'
                    }
                }
            ),
            200: openapi.Response(
                description="Подписка уже существует",
                examples={
                    'application/json': {
                        'detail': 'Вы уже подписаны на этот курс'
                    }
                }
            ),
            400: "Неверный ID курса",
            401: "Не авторизован",
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])

    def subscribe(self, request, pk=None):
        """Подписаться на обновления курса."""
        course = self.get_object()
        user = request.user
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            course=course,
            defaults={'is_active': True}
        )

        if not created and not subscription.is_active:
            subscription.is_active = True
            subscription.save()
            return Response({'detail': 'Подписка возобновлена'}, status=status.HTTP_200_OK)
        elif created:
            return Response({'detail': 'Вы подписались на курс'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'detail': 'Вы уже подписаны на этот курс'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    @swagger_auto_schema(
        method='post',
        operation_summary="Отписаться от курса",
        operation_description="Отмена подписки на обновления курса.",
        responses={
            200: openapi.Response(
                description="Успешная отписка",
                examples={
                    'application/json': {
                        'detail': 'Вы отписались от курса'
                    }
                }
            ),
            400: "Вы не подписаны на этот курс",
            401: "Не авторизован",
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])

    def unsubscribe(self, request, pk=None):
        """Отписаться от обновлений курса."""
        course = self.get_object()
        user = request.user

        try:
            subscription = Subscription.objects.get(user=user, course=course)
            subscription.is_active = False
            subscription.save()
            return Response({'detail': 'Вы отписались от курса'}, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({'detail': 'Вы не подписаны на этот курс'}, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet для управления подписками."""

    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Пользователь видит только свои подписки."""
        return Subscription.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LessonListCreateAPIView(generics.ListCreateAPIView):
    """Generic-класс для получения списка уроков и создания нового."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = LessonPagination

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        elif self.request.method == 'POST':
            return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or IsModerator().has_permission(self.request, self):
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveAPIView(generics.RetrieveAPIView):
    """Generic-класс для получения одного урока."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or IsModerator().has_permission(self.request, self):
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonUpdateAPIView(generics.UpdateAPIView):
    """Generic-класс для обновления урока."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or IsModerator().has_permission(self.request, self):
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)


class LessonDestroyAPIView(generics.DestroyAPIView):
    """Generic-класс для удаления урока."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Lesson.objects.all()
        if IsModerator().has_permission(self.request, self):
            return Lesson.objects.none()
        return Lesson.objects.filter(owner=user)


class CoursePaymentView(generics.RetrieveAPIView):
    """Представление для получения информации об оплате курса."""

    queryset = Course.objects.all()
    serializer_class = CoursePaymentSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Получить информацию об оплате курса",
        operation_description="Возвращает информацию о курсе для оплаты, включая публичный ключ Stripe и тестовые карты",
        responses={
            200: CoursePaymentSerializer,
            400: "Курс бесплатный",
            404: "Курс не найден",
        }
    )
    def get(self, request, *args, **kwargs):
        """Возвращает информацию о курсе для оплаты."""
        course = self.get_object()

        # Проверяем, является ли курс платным
        if not course.is_paid or course.price <= 0:
            return Response({
                'detail': 'Этот курс бесплатный, оплата не требуется'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(course)
        return Response(serializer.data)


class CreatePaymentSessionView(APIView):
    """Создание сессии оплаты в Stripe."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Создать сессию оплаты",
        operation_description="""
        Создает сессию оплаты для курса через Stripe.

        Возвращает ссылку для перенаправления пользователя к оплате.

        Перед созданием сессии автоматически создается продукт и цена в Stripe,
        если они еще не были созданы.
        """,
        request_body=StripeCheckoutSerializer,
        responses={
            201: openapi.Response(
                description="Сессия оплаты создана",
                examples={
                    'application/json': {
                        'payment_id': 1,
                        'stripe_session_id': 'cs_test_...',
                        'payment_url': 'https://checkout.stripe.com/pay/...',
                        'status': 'pending',
                        'message': 'Сессия оплаты создана. Перенаправьте пользователя по payment_url.'
                    }
                }
            ),
            400: "Курс бесплатный или уже куплен",
            404: "Курс не найден",
        }
    )
    def post(self, request, course_id):
        """
        Создает сессию оплаты для курса.

        Параметры:
        - course_id: ID курса для оплаты
        """
        # Получаем курс
        course = get_object_or_404(Course, id=course_id)

        # Проверяем, является ли курс платным
        if not course.is_paid or course.price <= 0:
            return Response({
                'detail': 'Этот курс бесплатный, оплата не требуется'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, не купил ли уже пользователь курс
        existing_payment = Payment.objects.filter(
            user=request.user,
            paid_course=course,
            status__in=['paid', 'pending']
        ).first()

        if existing_payment:
            return Response({
                'detail': 'Вы уже приобрели этот курс или платеж находится в обработке',
                'payment_id': existing_payment.id,
                'status': existing_payment.status
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем наличие Stripe ID у курса
        if not course.stripe_product_id or not course.stripe_price_id:
            # Создаем продукт и цену в Stripe
            try:
                product = StripeService.create_product(course)
                course.stripe_product_id = product.id

                price = StripeService.create_price(product.id, course.price)
                course.stripe_price_id = price.id
                course.save()
            except Exception as e:
                return Response({
                    'detail': f'Ошибка при создании продукта в Stripe: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Получаем кастомные URL из запроса
            serializer = StripeCheckoutSerializer(data=request.data)
            success_url = None
            cancel_url = None

            if serializer.is_valid():
                success_url = serializer.validated_data.get('success_url')
                cancel_url = serializer.validated_data.get('cancel_url')

            # Создаем сессию оплаты в Stripe
            session = StripeService.create_checkout_session(
                price_id=course.stripe_price_id,
                course=course,
                user=request.user,
                success_url=success_url,
                cancel_url=cancel_url
            )

            # Создаем запись о платеже в нашей системе
            payment = Payment.objects.create(
                user=request.user,
                paid_course=course,
                amount=course.price,
                payment_method='stripe',
                stripe_session_id=session.id,
                stripe_payment_link=session.url,
                status='pending'
            )

            return Response({
                'payment_id': payment.id,
                'stripe_session_id': session.id,
                'payment_url': session.url,
                'status': 'pending',
                'message': 'Сессия оплаты создана. Перенаправьте пользователя по payment_url.'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'detail': f'Ошибка при создании сессии оплаты: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckPaymentStatusView(APIView):
    """Проверка статуса оплаты."""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Проверить статус оплаты",
        operation_description="""
        Проверяет статус оплаты по ID сессии Stripe.

        Запрашивает актуальный статус у Stripe API и обновляет локальную запись платежа.
        """,
        request_body=PaymentStatusSerializer,
        responses={
            200: openapi.Response(
                description="Статус платежа",
                examples={
                    'application/json': {
                        'payment_id': 1,
                        'stripe_session_id': 'cs_test_...',
                        'payment_status': 'paid',
                        'status': 'paid',
                        'message': 'Оплата успешно завершена',
                        'paid_course': {
                            'id': 1,
                            'title': 'Название курса'
                        }
                    }
                }
            ),
            400: "Неверные данные",
            404: "Платеж не найден",
        }
    )
    def post(self, request):
        """
        Проверяет статус оплаты по ID сессии Stripe.

        Параметры:
        - session_id: ID сессии Stripe
        """
        serializer = PaymentStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data['session_id']

        try:
            # Получаем информацию о сессии из Stripe
            session = StripeService.retrieve_session(session_id)

            # Находим соответствующий платеж в нашей системе
            payment = Payment.objects.filter(
                stripe_session_id=session_id,
                user=request.user
            ).first()

            if not payment:
                return Response({
                    'detail': 'Платеж не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            # Обновляем статус платежа на основе данных Stripe
            payment_status = session.get('payment_status', 'unpaid')

            if payment_status == 'paid':
                payment.status = 'paid'
                payment.stripe_payment_intent_id = session.get('payment_intent')
                payment.save()
                status_message = 'Оплата успешно завершена'
            elif payment_status == 'unpaid':
                payment.status = 'pending'
                payment.save()
                status_message = 'Ожидание оплаты'
            else:
                payment.status = 'failed'
                payment.save()
                status_message = 'Оплата не удалась'

            return Response({
                'payment_id': payment.id,
                'stripe_session_id': session_id,
                'payment_status': payment_status,
                'status': payment.status,
                'message': status_message,
                'paid_course': {
                    'id': payment.paid_course.id,
                    'title': payment.paid_course.title
                } if payment.paid_course else None
            })

        except Exception as e:
            return Response({
                'detail': f'Ошибка при проверке статуса оплаты: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StripeWebhookView(APIView):
    """Обработчик вебхуков от Stripe."""

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Вебхук Stripe",
        operation_description="""
        Эндпоинт для получения вебхуков от Stripe.

        Используется для автоматического обновления статусов платежей.
        Требует настройки вебхука в панели управления Stripe.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description="Событие вебхука от Stripe"
        ),
        responses={
            200: "Вебхук успешно обработан",
            400: "Неверный запрос",
        }
    )
    def post(self, request):
        """
        Обрабатывает вебхуки от Stripe для обновления статусов платежей.
        """
        import json
        from django.http import HttpResponse

        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            # Верифицируем вебхук (требуется настроить вебхук в панели Stripe)
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Невалидный payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Невалидная подпись
            return HttpResponse(status=400)

        # Обрабатываем событие
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            # Находим платеж в нашей системе
            payment = Payment.objects.filter(
                stripe_session_id=session['id']
            ).first()

            if payment:
                payment.status = 'paid'
                payment.stripe_payment_intent_id = session.get('payment_intent')
                payment.save()

                # Здесь можно добавить логику предоставления доступа к курсу
                # Например, отправку уведомления пользователю

                print(f"Payment {payment.id} marked as paid via webhook")

        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']

            payment = Payment.objects.filter(
                stripe_session_id=session['id']
            ).first()

            if payment:
                payment.status = 'failed'
                payment.save()
                print(f"Payment {payment.id} expired via webhook")

        return HttpResponse(status=200)