from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, status, filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User, Payment
from .serializers import UserSerializer, PaymentSerializer
from .permissions import IsModerator, IsOwner
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомный view для получения JWT токенов."""

    @swagger_auto_schema(
        operation_summary="Аутентификация пользователя",
        operation_description="Получение JWT токенов по email и паролю",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='email',
                    description='Email пользователя'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='password',
                    description='Пароль пользователя'
                ),
            }
        ),
        responses={
            200: openapi.Response(
                description="Успешная аутентификация",
                examples={
                    'application/json': {
                        'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                        'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
                    }
                }
            ),
            401: "Неверные учетные данные",
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RegisterView(generics.CreateAPIView):
    """View для регистрации пользователей."""

    @swagger_auto_schema(
        operation_summary="Регистрация нового пользователя",
        operation_description="Создание нового аккаунта пользователя",
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response(
                description="Успешная регистрация",
                examples={
                    'application/json': {
                        'id': 1,
                        'email': 'user@example.com',
                        'first_name': 'Иван',
                        'last_name': 'Иванов'
                    }
                }
            ),
            400: "Ошибка валидации",
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'paid_course': ['exact'],
        'paid_lesson': ['exact'],
        'payment_method': ['exact'],
    }
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]