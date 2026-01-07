from rest_framework import serializers
from users.models import Payment
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """для уроков"""

    class Meta:
        model = Lesson
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    """для курсов с количеством уроков и списком уроков"""
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'preview', 'description', 'lessons_count', 'lessons']

    def get_lessons_count(self, obj):
        return obj.lessons.count()
