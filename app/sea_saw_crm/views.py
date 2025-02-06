from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F
from django.db.models.functions import Coalesce, TruncDate
from django.utils.timezone import make_aware
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from download.views import DownloadView
from .filters import ContractFilter, ContactFilter, CompanyFilter, OrderFilter
from .metadata import CustomMetadata
from .mixins import RoleFilterMixin
from .models import Contact, Company, Order, Contract, Field, OrderProduct
from .pagination import CustomPageNumberPagination
from .permissions import CustomDjangoModelPermission
from .serializers import (
    ContactSerializer, CompanySerializer,
    ContractSerializer, FieldSerializer, OrderProductSerializer, OrderSerializer4Prod
)

LOOKUP_TYPES = [
    "exact", "iexact", "contains", "icontains", "in",
    "gt", "lt", "gte", "lte", "startswith", "istartswith",
    "endswith", "iendswith", "range", "date", "year",
    "month", "day", "week_day", "isnull", "search",
    "regex", "iregex", "hour", "minute", "second", "time"
]
LOOKUP_PATTERN = r'__(?:' + '|'.join(LOOKUP_TYPES) + r')$'

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [CustomDjangoModelPermission]
    pagination_class = CustomPageNumberPagination
    metadata_class = CustomMetadata

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.username)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user.username)


class FieldListView(ListAPIView):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer


class ContactViewSet(RoleFilterMixin, BaseViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    filter_backends = (SearchFilter, filters.DjangoFilterBackend)
    search_fields = ['^first_name', '^last_name']


class CompanyViewSet(BaseViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filterset_class = CompanyFilter
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend)


class ContractViewSet(RoleFilterMixin, BaseViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    filterset_class = ContractFilter
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend)
    ordering_fields = ["orders__pk"]


class ProductViewSet(BaseViewSet):
    queryset = OrderProduct.objects.all()
    serializer_class = OrderProductSerializer


class OrderViewSet(BaseViewSet):
    queryset = Order.objects.all()
    filterset_class = OrderFilter
    filter_backends = (OrderingFilter, filters.DjangoFilterBackend)
    serializer_class = OrderSerializer4Prod
    ordering_fields = ['pk', 'created_at', 'updated_at']


class BaseCompareStatsByMonth(APIView):
    permission_classes = [IsAuthenticated]
    model = None  # Override this in subclasses

    @staticmethod
    def get_date_ranges():
        today = datetime.today()
        first_day_this_month = today.replace(day=1)
        last_day_this_month = (first_day_this_month + relativedelta(months=1)) - relativedelta(days=1)
        first_day_last_month = first_day_this_month - relativedelta(months=1)
        last_day_last_month = first_day_this_month - relativedelta(days=1)

        return {
            "this_month": (make_aware(first_day_this_month), make_aware(last_day_this_month)),
            "last_month": (make_aware(first_day_last_month), make_aware(last_day_last_month)),
        }

    def get_base_queryset(self):
        return self.model.objects.all()

    def get_queryset(self):
        base_queryset = self.get_base_queryset()
        date_range = self.get_date_ranges()
        queryset_this_month = base_queryset.filter(created_at__range=date_range["this_month"])
        queryset_last_month = base_queryset.filter(created_at__range=date_range["last_month"])
        return queryset_this_month, queryset_last_month

    def get(self, request):
        raise NotImplementedError("Subclasses must implement the `get` method.")


class ContractStats(BaseCompareStatsByMonth):
    model = Contract

    def get_base_queryset(self):
        user = self.request.user
        user_groups = user.groups.values_list('name', flat=True)
        base_queryset = super().get_base_queryset()
        # Admin user can see all contract related stats
        if user.is_superuser or user.is_staff:
            return base_queryset
        # Sale user only see stats based on their permissin scope
        if 'Sale' in user_groups:
            return base_queryset.filter(owner__in=user.get_all_visible_users())
        # Production can also see all stats, this feature will be changed in the future
        if 'Production' in user_groups:
            return base_queryset
        return base_queryset.none()

    def get(self, request):
        contracts_this_month, contracts_last_month = self.get_queryset()
        data = {
            "contracts_this_month_count": contracts_this_month.count(),
            "contracts_last_month_count": contracts_last_month.count(),
        }
        return Response(data)


class OrderStats(BaseCompareStatsByMonth):
    model = Order

    def get_base_queryset(self):
        user = self.request.user
        user_groups = user.groups.values_list('name', flat=True)
        base_queryset = super().get_base_queryset()
        if user.is_superuser or user.is_staff:
            return base_queryset
        if 'Sale' in user_groups:
            return base_queryset.filter(owner__in=user.get_all_visible_users())
        if 'Production' in user_groups:
            return base_queryset
        return base_queryset.none()

    @staticmethod
    def get_income(queryset):
        return queryset.aggregate(
            total_income=Coalesce(Sum(F('deposit') + F('balance')), Decimal(0.0))
        )['total_income']

    def get(self, request):
        orders_this_month, orders_last_month = self.get_queryset()
        user_groups = self.request.user.groups.values_list('name', flat=True)

        # 如果用户是 "Production" 用户并且没有其他角色，直接返回不含 income 的数据
        if 'Production' in user_groups and len(user_groups) == 1:
            data = {
                "orders_this_month_count": orders_this_month.count(),
                "orders_last_month_count": orders_last_month.count(),
            }
        else:
            # 对于非 Production 用户，计算 income
            data = {
                "orders_this_month_count": orders_this_month.count(),
                "orders_last_month_count": orders_last_month.count(),
                "orders_this_month_income": self.get_income(orders_this_month),
                "orders_last_month_income": self.get_income(orders_last_month),
            }

        return Response(data)


class OrderStatsByMonth(APIView):
    model = Order
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_orders_grouped_by_etd(queryset):
        grouped_orders = defaultdict(list)
        orders = queryset.annotate(etd_date=TruncDate('etd')).values('etd_date', 'order_code', 'stage', 'owner__username')

        for order in orders:
            etd_date = order['etd_date'].strftime('%Y-%m-%d') if order['etd_date'] else None
            if etd_date:
                grouped_orders[etd_date].append({
                    "order_code": order['order_code'],
                    "stage": order['stage'],
                    "owner": order['owner__username'],
                })

        return dict(grouped_orders)

    def get(self, request):
        year_month = request.query_params.get('date', None)
        if not year_month:
            today = datetime.today()
            year_month = f"{today.year}-{today.month:02d}"

        try:
            year, month = map(int, year_month.split('-'))
        except ValueError:
            return Response({"error": "Invalid 'date' format. Expected 'YYYY-MM'."},
                            status=status.HTTP_400_BAD_REQUEST)

        queryset = self.model.objects.all()
        orders_for_month = queryset.filter(etd__year=year, etd__month=month)
        grouped_orders = self.get_orders_grouped_by_etd(orders_for_month)
        return Response(grouped_orders)


class DownloadTaskView(DownloadView):
    # 使用自定义的权限类，确保用户具有适当的权限
    # Using custom permission class to ensure the user has appropriate permissions
    permission_classes = [IsAuthenticated, CustomDjangoModelPermission]

    # 映射不同对象类型到相应的模型和序列化器
    # Map different object types to corresponding models and serializers
    download_obj_mapping = {
        "contracts": {
            "model": "sea_saw_crm.Contract",
            "serializer": "sea_saw_crm.ContractSerializer"
        },
        "orders": {
            "model": "sea_saw_crm.Order",
            "serializer": "sea_saw_crm.OrderSerializer4Prod"
        }
    }

    def get_filters(self, request):
        """
        获取并根据用户角色动态修改筛选条件。
        Get and dynamically modify filter conditions based on user roles.
        """
        filters_dict = super().get_filters(request)  # 获取父类的 filters 字典
        # Get the filters dictionary from the parent class
        user = request.user

        # 如果是匿名用户，返回空查询条件
        # If the user is anonymous, return empty filter conditions
        if user.is_anonymous:
            filters_dict["id__in"] = []  # 不返回任何记录，类似于 filters.none()
            return filters_dict

        # 如果是管理员或超级用户，返回所有数据的过滤条件
        # If the user is an admin or superuser, return all data's filter conditions
        if user.is_superuser or user.is_staff:
            return filters_dict

        # 非管理员用户，基于用户的可见性权限来过滤
        # For non-admin users, filter based on their visibility permissions
        visible_users = user.get_all_visible_users()
        filters_dict["owner__in"] = visible_users  # 增加过滤条件，限制查询可见的用户
        # Add filter condition to restrict query to visible users

        return filters_dict




