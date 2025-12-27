from rest_framework.viewsets import ModelViewSet

from ..serializers import FieldSerializer
from ..models import Field
from ..permissions import FieldPermission
from rest_framework.permissions import IsAuthenticated


class FieldListView(ModelViewSet):
    """View set for Field model"""

    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated, FieldPermission]
