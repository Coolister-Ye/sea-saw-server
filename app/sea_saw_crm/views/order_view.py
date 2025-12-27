from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError

from ..models import Order
from ..metadata import OrderMetadata
from ..constants import OrderStatus
from ..serializers import (
    OrderSerializerForAdmin,
    OrderSerializerForProduction,
    OrderSerializerForSales,
    OrderSerializerForWarehouse,
)
from ..permissions import IsAdmin, IsProduction, IsSale, IsWarehouse, CanTransitionOrder


class ProxyOrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    metadata_class = OrderMetadata
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    permission_classes = [
        IsAuthenticated,
        IsAdmin | IsSale | IsProduction | IsWarehouse,
    ]

    role_serializer_map = {
        "ADMIN": OrderSerializerForAdmin,
        "SALE": OrderSerializerForSales,
        "PRODUCTION": OrderSerializerForProduction,
        "WAREHOUSE": OrderSerializerForWarehouse,
    }

    def get_serializer_class(self):
        role = getattr(self.request.user.role, "role_type", None)
        serializer = self.role_serializer_map.get(role)
        if not serializer:
            raise PermissionDenied("No serializer for this role")
        return serializer

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        role = getattr(user.role, "role_type", None)

        if role == "SALE":
            get_visibles = getattr(user, "get_all_visible_users", None)
            visible_users = get_visibles() if callable(get_visibles) else [user]
            return qs.filter(owner__in=visible_users)

        if role == "PRODUCTION":
            return qs.filter(status__in=OrderStatus.PRODUCTION_VISIBLE)

        if role == "WAREHOUSE":
            return qs.filter(status__in=OrderStatus.WAREHOUSE_VISIBLE)

        return qs

    # -----------------------------
    # Custom actions
    # -----------------------------
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsProduction | IsAdmin],
    )
    def create_production(self, request, pk=None):
        order = self.get_object()
        try:
            order.create_production(user=request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 根据当前用户角色选择 Order serializer
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, IsWarehouse | IsAdmin],
    )
    def create_outbound(self, request, pk=None):
        order = self.get_object()
        try:
            order.create_outbound(user=request.user)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 根据当前用户角色选择 Order serializer
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
            CanTransitionOrder,
        ],
    )
    def transition(self, request, pk=None):
        order = self.get_object()
        action_name = request.data.get("action")

        if not action_name:
            return Response(
                {"detail": "action is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order.transition(action_name, user=request.user)
        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(order)
        return Response(serializer.data)
