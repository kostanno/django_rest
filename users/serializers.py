from rest_framework import serializers
from .models import Payment
from lms.serializers import CourseSerializer, LessonSerializer

class PaymentSerializer(serializers.ModelSerializer):
    """ для платежей"""

    paid_course_detail = CourseSerializer(source='оплата за курс', read_only=True)
    paid_lesson_detail = LessonSerializer(source='оплата за урок', read_only=True)
    user_email = serializers.EmailField(source='ваш емаил', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id',
            'user',
            'user_email',
            'payment_date',
            'paid_course',
            'paid_lesson',
            'paid_course_detail',
            'paid_lesson_detail',
            'amount',
            'payment_method'
        ]