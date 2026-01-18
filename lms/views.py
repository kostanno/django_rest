from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Course, Lesson, Subscription
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer
from .permissions import IsModerator
from .paginators import LessonPagination, CoursePagination


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для CRUD операций с курсами."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def get_permissions(self):

        if self.action == 'list' or self.action == 'retrieve':
            return [IsAuthenticated()]
        elif self.action == 'create':
            return [IsAuthenticated(), IsNotModerator()]
        elif self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), IsOwnerOrModerator]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsOwnerAndNotModerator]
        else:
            return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        """Возвращаем queryset в зависимости от прав пользователя."""
        user = self.request.user
        if user.is_superuser or IsModerator().has_permission(self.request, self):
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании курса автоматически устанавливаем владельца."""
        serializer.save(owner=self.request.user)

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