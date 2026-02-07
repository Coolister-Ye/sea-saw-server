from rest_framework.generics import ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from sea_saw_preference.models import UserColumnPreference
from sea_saw_preference.serializers import UserColumnPreferenceSerializer


class UserColumnPreferenceViewset(ListCreateAPIView):
    queryset = UserColumnPreference.objects.all()
    serializer_class = UserColumnPreferenceSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'table_name'  # Use table_name as the lookup field

    def create(self, request, *args, **kwargs):
        # Get data from the request
        table_name = request.data.get('table_name')
        column_pref = request.data.get('column_pref')

        # Ensure required fields are present
        if not table_name or column_pref is None:
            return Response({"detail": "Missing required fields: table_name or column_order"}, status=400)

        # Use update_or_create to update or create the preference for the current user and table_name
        preference, created = UserColumnPreference.objects.update_or_create(
            user=request.user,
            table_name=table_name,
            defaults={'column_pref': column_pref},  # Assuming 'column_order' is the JSON field
        )

        # Serialize and return the data
        serializer = self.get_serializer(preference)
        return Response(serializer.data, status=201 if created else 200)

    def list(self, request, *args, **kwargs):
        # Retrieve table_name from URL parameters
        table_name = self.kwargs.get(self.lookup_field)

        # Attempt to find the user column preference for the given table_name
        preference = UserColumnPreference.objects.filter(user=request.user, table_name=table_name).first()

        # If no preference is found, return an empty response
        if not preference:
            return Response({})  # Empty JSON response if no preference is found

        # Serialize and return the preference data
        serializer = self.get_serializer(preference)
        return Response(serializer.data)
