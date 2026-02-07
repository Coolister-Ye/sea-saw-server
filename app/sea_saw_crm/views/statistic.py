from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from django.utils.timezone import now
from dateutil.relativedelta import relativedelta

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db.models import Sum, F, DecimalField, CharField, Value
from django.db.models.functions import (
    Coalesce,
    TruncDate,
    ExtractYear,
    ExtractMonth,
    Cast,
    Concat,
    LPad,
)

from sea_saw_sales.models import Order


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
