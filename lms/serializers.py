from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import YouTubeURLValidator


class SubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'course', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        subscription, created = Subscription.objects.get_or_create(
            user=validated_data['user'],
            course=validated_data['course'],
            defaults={'is_active': True}
        )

        if not created:
            subscription.is_active = True
            subscription.save()

        return subscription

class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для уроков с валидацией YouTube ссылок."""

    # Используем классовый валидатор
    video_link = serializers.URLField(
        validators=[YouTubeURLValidator()],
        help_text="Ссылка на видео. Разрешены только youtube.com и youtu.be"
    )

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'preview', 'video_link', 'course', 'owner']
        extra_kwargs = {
            'owner': {'read_only': True},
        }

    def validate_video_link(self, value):
        """Дополнительная валидация для video_link с использованием классового валидатора."""
        validator = YouTubeURLValidator()
        return validator(value)

    def validate(self, attrs):
        """Валидация на уровне объекта."""
        return attrs


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курсов."""

    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'lessons_count', 'lessons', 'is_subscribed', 'owner']
        extra_kwargs = {
            'owner': {'read_only': True},
        }

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на курс."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj,
                is_active=True
            ).exists()
        return False


class CoursePaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для оплаты курса."""

    stripe_public_key = serializers.SerializerMethodField()
    test_cards = serializers.SerializerMethodField()
    is_purchased = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price',
            'stripe_product_id', 'stripe_price_id',
            'stripe_public_key', 'test_cards', 'is_purchased'
        ]
        read_only_fields = ['stripe_product_id', 'stripe_price_id']

    def get_stripe_public_key(self, obj):
        from django.conf import settings
        return settings.STRIPE_PUBLIC_KEY

    def get_test_cards(self, obj):
        """Возвращает тестовые карты для Stripe."""
        return StripeService.get_test_cards()

    def get_is_purchased(self, obj):
        """Проверяет, купил ли текущий пользователь курс."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from users.models import Payment
            return Payment.objects.filter(
                user=request.user,
                paid_course=obj,
                status='paid'
            ).exists()
        return False


class StripeCheckoutSerializer(serializers.Serializer):
    """Сериализатор для создания сессии оплаты в Stripe."""

    success_url = serializers.URLField(
        required=False,
        help_text='URL для перенаправления после успешной оплаты'
    )
    cancel_url = serializers.URLField(
        required=False,
        help_text='URL для перенаправления при отмене оплаты'
    )

    class Meta:
        fields = ['success_url', 'cancel_url']


class PaymentStatusSerializer(serializers.Serializer):
    """Сериализатор для проверки статуса оплаты."""

    session_id = serializers.CharField(
        max_length=255,
        help_text='ID сессии Stripe'
    )

    class Meta:
        fields = ['session_id']