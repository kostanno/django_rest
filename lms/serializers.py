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
        extra_kwargs = {'owner': {'read_only': True},}


    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj,
                is_active=True
            ).exists()
        return False

    def validate(self, attrs):
        """Пример валидации курса."""
        if attrs.get('is_paid', False) and not attrs.get('description'):
            raise serializers.ValidationError({
                'description': 'Платный курс должен иметь описание'
            })
        return attrs