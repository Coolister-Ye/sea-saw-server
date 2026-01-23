"""
ContentType lookup view for frontend.
Provides ContentType IDs for different models.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType


class ContentTypeView(APIView):
    """
    API endpoint to get ContentType IDs for models.

    GET /api/sea-saw-crm/content-types/
    Returns: { "order": 15, "purchaseorder": 23, ... }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return ContentType IDs for commonly used models."""
        from ..models.order import Order
        from ..models.purchase import PurchaseOrder
        from ..models.production import ProductionOrder
        from ..models.outbound import OutboundOrder
        from ..models.pipeline import Pipeline

        content_types = {
            "order": ContentType.objects.get_for_model(Order).id,
            "pipeline": ContentType.objects.get_for_model(Pipeline).id,
            "purchaseorder": ContentType.objects.get_for_model(PurchaseOrder).id,
            "productionorder": ContentType.objects.get_for_model(ProductionOrder).id,
            "outboundorder": ContentType.objects.get_for_model(OutboundOrder).id,
        }

        return Response(content_types)
