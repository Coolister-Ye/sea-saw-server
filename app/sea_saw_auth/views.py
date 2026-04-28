from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.generics import CreateAPIView, UpdateAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView

from sea_saw_base.metadata import BaseMetadata
from sea_saw_auth.filters import AdminUserFilter
from sea_saw_auth.models import User, Role
from sea_saw_auth.serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    AdminUserSerializer,
    AdminUserCreateSerializer,
    RoleSerializer,
)
from sea_saw_auth.throttles import LoginRateThrottle, RegisterRateThrottle


class ThrottledTokenObtainPairView(BaseTokenObtainPairView):
    throttle_classes = [LoginRateThrottle]


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
    authentication_classes = []  # No authentication required for registration
    throttle_classes = [RegisterRateThrottle]
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


class AdminUserViewSet(ModelViewSet):
    """Admin-only ViewSet for user management"""

    queryset = User.objects.select_related("role").all().order_by("id")
    permission_classes = [IsAdminUser]
    metadata_class = BaseMetadata
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = AdminUserFilter
    search_fields = ["^username", "^email"]

    def get_serializer_class(self):
        if self.action == "create":
            return AdminUserCreateSerializer
        return AdminUserSerializer

    @action(detail=True, methods=["post"], url_path="toggle-active")
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return Response(AdminUserSerializer(user).data)


class RoleViewSet(ModelViewSet):
    """Admin-only ViewSet for role management"""

    queryset = Role.objects.select_related("parent").all()
    permission_classes = [IsAdminUser]
    metadata_class = BaseMetadata
    serializer_class = RoleSerializer
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ["^role_name"]
