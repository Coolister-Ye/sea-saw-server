from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sea_saw_preference.models import UserColumnPreference
from sea_saw_preference.serializers import UserColumnPreferenceSerializer


class UserColumnPreferenceViewset(ListCreateAPIView):
    queryset = UserColumnPreference.objects.all()
    serializer_class = UserColumnPreferenceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "table_name"

    def create(self, request, *args, **kwargs):
        table_name = request.data.get("table_name")
        column_pref = request.data.get("column_pref")

        if not table_name or column_pref is None:
            return Response({"detail": "Missing required fields: table_name or column_order"}, status=400)

        preference, created = UserColumnPreference.objects.update_or_create(
            user=request.user,
            table_name=table_name,
            defaults={"column_pref": column_pref},
        )

        serializer = self.get_serializer(preference)
        return Response(serializer.data, status=201 if created else 200)

    def list(self, request, *args, **kwargs):
        table_name = self.kwargs.get(self.lookup_field)
        preference = UserColumnPreference.objects.filter(user=request.user, table_name=table_name).first()

        if not preference:
            return Response({})

        serializer = self.get_serializer(preference)
        return Response(serializer.data)
