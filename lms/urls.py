from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonListCreateAPIView,
    LessonRetrieveAPIView,
    LessonUpdateAPIView,
    LessonDestroyAPIView,
    SubscriptionViewSet,
    CoursePaymentView,
    CreatePaymentSessionView,
    CheckPaymentStatusView,
    StripeWebhookView
)

app_name = 'lms'

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('lessons/', LessonListCreateAPIView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', LessonRetrieveAPIView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/update/', LessonUpdateAPIView.as_view(), name='lesson-update'),
    path('lessons/<int:pk>/delete/', LessonDestroyAPIView.as_view(), name='lesson-delete'),
    path('courses/<int:pk>/payment-info/', CoursePaymentView.as_view(), name='course-payment-info'),
    path('courses/<int:pk>/create-payment/', CreatePaymentSessionView.as_view(), name='create-payment'),
    path('check-payment-status/', CheckPaymentStatusView.as_view(), name='check-payment-status'),
    path('stripe-webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]