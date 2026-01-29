from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import CreateAPIView, UpdateAPIView

from sea_saw_auth.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
)


class UserDetailView(APIView):
    """Get current user's profile"""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserRegisterView(CreateAPIView):
    """Register a new user account"""

    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication to bypass CSRF check
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Return user data without password
        user_serializer = UserSerializer(user)
        return Response(
            {
                "message": "User registered successfully",
                "user": user_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileUpdateView(UpdateAPIView):
    """Update current user's profile"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def get_object(self):
        """Return current authenticated user"""
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Return updated user data
        user_serializer = UserSerializer(instance)
        return Response(
            {
                "message": "Profile updated successfully",
                "user": user_serializer.data,
            }
        )
