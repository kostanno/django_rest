from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment
from users.serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """ля работы с платежами"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]

    filterset_fields = {
        'paid_course': ['exact'],
        'paid_lesson': ['exact'],
        'payment_method': ['exact'],
    }
    ordering_fields = ['payment_date', 'amount']
    ordering = ['-payment_date']