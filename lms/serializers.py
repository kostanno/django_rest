from rest_framework import serializers
from .models import Course, Lesson, Subscription
from .validators import validate_youtube_only, YouTubeURLValidator


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для уроков"""
    video_link = serializers.URLField(
        validators=[validate_youtube_only]
    )

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'description', 'preview', 'video_link', 'course', 'owner']
        extra_kwargs = {
            'owner': {'read_only': True},
            'video_link': {'validators': [validate_youtube_only]}
        }

    def validate_video_link(self, value):
        return validate_youtube_only(value)


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'lessons_count', 'lessons', 'is_subscribed', 'owner']
        extra_kwargs = {
            'owner': {'read_only': True},
        }
        validators = [
            YouTubeURLValidator(field='lessons')
        ]

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