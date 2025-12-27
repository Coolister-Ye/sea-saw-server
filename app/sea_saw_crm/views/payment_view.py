# sea_saw_crm/views/payment.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from ..models.payment import PaymentRecord
from ..serializers.payment import PaymentRecordSerializer
from ..permissions import CanManagePayment
from ..metadata import BaseMetadata


class PaymentRecordViewSet(ModelViewSet):
    queryset = PaymentRecord.objects.select_related("order")
    serializer_class = PaymentRecordSerializer
    permission_classes = [
        IsAuthenticated,
        CanManagePayment,
    ]
    filter_backends = [
        DjangoFilterBackend,
        OrderingFilter,
    ]
    metadata_class = BaseMetadata
    filterset_fields = ["order", "currency", "payment_method"]
    ordering_fields = ["payment_date", "amount", "created_at"]
    ordering = ["-payment_date"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user.role, "role_type", None)

        if role == "SALE":
            return qs.filter(order__owner=user)

        return qs

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            owner=self.request.user,
        )
