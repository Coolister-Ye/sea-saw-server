from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F, DecimalField, CharField, Func, Value
from django.db.models.functions import (
    Coalesce,
    TruncDate,
    ExtractYear,
    ExtractMonth,
    Cast,
    Concat,
    LPad,
)
from django.utils.timezone import make_aware, now
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
    ContactSerializer,
    CompanySerializer,
    ContractSerializer,
    FieldSerializer,
    OrderProductSerializer,
    OrderSerializer4Prod,
)

LOOKUP_TYPES = [
    "exact",
    "iexact",
    "contains",
    "icontains",
    "in",
    "gt",
    "lt",
    "gte",
    "lte",
    "startswith",
    "istartswith",
    "endswith",
    "iendswith",
    "range",
    "date",
    "year",
    "month",
    "day",
    "week_day",
    "isnull",
    "search",
    "regex",
    "iregex",
    "hour",
    "minute",
    "second",
    "time",
]
LOOKUP_PATTERN = r"__(?:" + "|".join(LOOKUP_TYPES) + r")$"


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [CustomDjangoModelPermission]
    pagination_class = CustomPageNumberPagination
    metadata_class = CustomMetadata

    # def perform_create(self, serializer):
    #     serializer.save(created_by=self.request.user.username)
    #
    # def perform_update(self, serializer):
    #     serializer.save(updated_by=self.request.user.username)


class FieldListView(ListAPIView):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer


class ContactViewSet(RoleFilterMixin, BaseViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_class = ContactFilter
    filter_backends = (SearchFilter, filters.DjangoFilterBackend)
    search_fields = ["^first_name", "^last_name"]


class CompanyViewSet(RoleFilterMixin, BaseViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    filterset_class = CompanyFilter
    filter_backends = (OrderingFilter, SearchFilter, filters.DjangoFilterBackend)
    search_fields = ["^company_name"]


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
    ordering_fields = ["pk", "created_at", "updated_at"]


class BaseStatsAPIView(APIView):
    """抽取通用统计逻辑"""

    model = None

    def get_queryset(self):
        """根据用户权限获取数据集"""
        user = self.request.user
        user_groups = set(user.groups.values_list("name", flat=True))
        base_queryset = self.model.objects.all().only("created_at")

        if user.is_superuser or user.is_staff:
            return base_queryset

        if "Sale" in user_groups:
            return base_queryset.filter(owner__in=user.get_all_visible_users())

        if "Production" in user_groups:
            return base_queryset

        return base_queryset.none()

    def get_stats(self, value_field, period="month", lookback=3):
        """
        通用的统计方法
        :param value_field: 需要统计的字段
        :param period: "month" 或 "year"
        :param lookback: 回溯时间，默认为 3（月/年）
        """
        filter_time = now() - relativedelta(**{f"{period}s": lookback})
        queryset = self.get_queryset().filter(
            created_at__gte=filter_time, deleted__isnull=True
        )

        if period == "month":
            queryset = queryset.annotate(
                year=ExtractYear("created_at"),
                month=Cast(ExtractMonth("created_at"), output_field=CharField()),
                formatted_month=LPad("month", 2, Value("0")),
                date=Concat(
                    "year", Value("-"), "formatted_month", output_field=CharField()
                ),
            )
        else:
            queryset = queryset.annotate(
                date=Cast(ExtractYear("created_at"), output_field=CharField())
            )

        return queryset.values("date").annotate(
            total=Coalesce(Sum(value_field, output_field=DecimalField()), Decimal(0.0))
        )


class ContractStats(BaseStatsAPIView):
    model = Contract

    def get(self, request):
        data = {
            "contracts_count_by_month": self.get_stats(
                Value(1), period="month", lookback=3
            ),
            "contracts_count_by_year": self.get_stats(
                Value(1), period="year", lookback=3
            ),
        }
        return Response(data)


class OrderStats(BaseStatsAPIView):
    model = Order

    def get(self, request):
        user_groups = set(request.user.groups.values_list("name", flat=True))

        data = {
            "orders_count_by_month": self.get_stats(
                Value(1), period="month", lookback=3
            ),
            "orders_count_by_year": self.get_stats(Value(1), period="year", lookback=3),
        }

        if "Production" not in user_groups or len(user_groups) > 1:
            data.update(
                {
                    "orders_received_by_month": self.get_stats(
                        Coalesce(F("balance"), Decimal(0.0))
                        + Coalesce(F("deposit"), Decimal(0.0)),
                        period="month",
                        lookback=3,
                    ),
                    "orders_receivable_by_year": self.get_stats(
                        Coalesce(F("total_amount"), Decimal(0.0))
                        - Coalesce(F("balance"), Decimal(0.0))
                        - Coalesce(F("deposit"), Decimal(0.0)),
                        period="year",
                        lookback=3,
                    ),
                    "orders_total_amount_by_year": self.get_stats(
                        F("total_amount"), period="year", lookback=3
                    ),
                    "orders_total_amount_by_month": self.get_stats(
                        F("total_amount"), period="month", lookback=3
                    ),
                    "orders_received_by_year": self.get_stats(
                        Coalesce(F("balance"), Decimal(0.0))
                        + Coalesce(F("deposit"), Decimal(0.0)),
                        period="year",
                        lookback=3,
                    ),
                }
            )

        return Response(data)


class OrderStatsByMonth(APIView):
    model = Order
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_orders_grouped_by_etd(queryset):
        grouped_orders = defaultdict(list)
        orders = queryset.annotate(etd_date=TruncDate("etd")).values(
            "etd_date", "order_code", "stage", "owner__username"
        )

        for order in orders:
            etd_date = (
                order["etd_date"].strftime("%Y-%m-%d") if order["etd_date"] else None
            )
            if etd_date:
                grouped_orders[etd_date].append(
                    {
                        "order_code": order["order_code"],
                        "stage": order["stage"],
                        "owner": order["owner__username"],
                    }
                )

        return dict(grouped_orders)

    def get(self, request):
        year_month = request.query_params.get("date", None)
        if not year_month:
            today = datetime.today()
            year_month = f"{today.year}-{today.month:02d}"

        try:
            year, month = map(int, year_month.split("-"))
        except ValueError:
            return Response(
                {"error": "Invalid 'date' format. Expected 'YYYY-MM'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = self.request.user
        user_groups = user.groups.values_list("name", flat=True)

        if user.is_superuser or user.is_staff or "Production" in user_groups:
            queryset = self.model.objects.all()
        elif "Sale" in user_groups:
            queryset = self.model.objects.filter(owner__in=user.get_all_visible_users())
        else:
            queryset = self.model.objects.none()

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
            "serializer": "sea_saw_crm.ContractSerializer",
        },
        "orders": {
            "model": "sea_saw_crm.Order",
            "serializer": "sea_saw_crm.OrderSerializer4Prod",
        },
    }

    def get_filters(self, request):
        """
        获取并根据用户角色动态修改筛选条件。
        Get and dynamically modify filter conditions based on user roles.
        """
        filters_dict = super().get_filters(request)  # 获取父类的 filters 字典
        # Get the filters dictionary from the parent class
        user = request.user
        user_groups = set(user.groups.values_list("name", flat=True))

        # 如果是匿名用户，返回空查询条件
        # If the user is anonymous, return empty filter conditions
        if user.is_anonymous:
            filters_dict["id__in"] = []  # 不返回任何记录，类似于 filters.none()
            return filters_dict

        # 如果是管理员或超级用户，返回所有数据的过滤条件
        # If the user is an admin or superuser, return all data's filter conditions
        if user.is_superuser or user.is_staff:
            return filters_dict

        if "Production" in user_groups:
            return filters_dict

        # 非管理员用户，基于用户的可见性权限来过滤
        # For non-admin users, filter based on their visibility permissions
        visible_users = user.get_all_visible_users()
        visible_users = [user.pk for user in visible_users]
        filters_dict["owner__pk__in"] = (
            visible_users  # 增加过滤条件，限制查询可见的用户
        )
        # Add filter condition to restrict query to visible users

        return filters_dict
