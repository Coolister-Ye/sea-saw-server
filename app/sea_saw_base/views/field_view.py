from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from sea_saw_base.models import Field
from sea_saw_base.serializers import FieldSerializer
from sea_saw_base.permissions import FieldPermission


class FieldListView(ModelViewSet):
    """View set for Field model"""

    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated, FieldPermission]
