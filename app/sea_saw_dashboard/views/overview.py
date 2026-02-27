from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.db.models import Sum, F, Value, DecimalField, CharField
from django.db.models.functions import (
    Coalesce,
    ExtractYear,
    ExtractMonth,
    Cast,
    Concat,
    LPad,
)
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sea_saw_sales.models import Order
from sea_saw_sales.models.enums import OrderStatusType


class OverviewStatsView(APIView):
    """
    全局概览报表视图

    GET /api/dashboard/overview/

    返回跨模块的汇总统计数据，供首页仪表盘使用。
    当前包含：
      - 近 12 个月订单数量（按月，仅 active/completed）
      - 近 3 年订单数量（按年，仅 active/completed）
      - 近 3 年订单总额（按年，非生产角色可见）
    """

    permission_classes = [IsAuthenticated]

    ACTIVE_STATUSES = [OrderStatusType.ACTIVE, OrderStatusType.COMPLETED]

    def _get_order_queryset(self, user_groups):
        user = self.request.user
        qs = Order.objects.filter(deleted__isnull=True)

        if user.is_superuser or user.is_staff:
            return qs
        if "Sale" in user_groups:
            return qs.filter(owner__in=user.get_all_visible_users())
        if "Production" in user_groups:
            return qs
        return qs.none()

    @staticmethod
    def _annotate_period(queryset, period):
        if period == "month":
            return queryset.annotate(
                date=Concat(
                    Cast(ExtractYear("created_at"), output_field=CharField()),
                    Value("-"),
                    LPad(
                        Cast(ExtractMonth("created_at"), output_field=CharField()),
                        2,
                        Value("0"),
                    ),
                    output_field=CharField(),
                )
            )
        return queryset.annotate(
            date=Cast(ExtractYear("created_at"), output_field=CharField())
        )

    @staticmethod
    def _generate_periods(period, lookback):
        """生成所有应返回的时间段标签，用于补零。"""
        current = now()
        if period == "month":
            return [
                f"{(current - relativedelta(months=i)).year}-{(current - relativedelta(months=i)).month:02d}"
                for i in range(lookback - 1, -1, -1)
            ]
        return [
            str((current - relativedelta(years=i)).year)
            for i in range(lookback - 1, -1, -1)
        ]

    def _aggregate(self, queryset, expression, period, lookback):
        since = now() - relativedelta(**{f"{period}s": lookback})
        qs = self._annotate_period(queryset.filter(created_at__gte=since), period)
        results = {
            row["date"]: row["total"]
            for row in qs.values("date").annotate(
                total=Coalesce(
                    Sum(expression, output_field=DecimalField()), Decimal("0.0")
                )
            )
        }
        periods = self._generate_periods(period, lookback)
        return [{"date": p, "total": results.get(p, Decimal("0.0"))} for p in periods]

    def get(self, request):
        user_groups = set(request.user.groups.values_list("name", flat=True))
        order_qs = self._get_order_queryset(user_groups)
        active_order_qs = order_qs.filter(status__in=self.ACTIVE_STATUSES)

        data = {
            "orders_count_by_month": self._aggregate(
                active_order_qs, Value(1), period="month", lookback=12
            ),
            "orders_count_by_year": self._aggregate(
                active_order_qs, Value(1), period="year", lookback=3
            ),
        }

        # 生产组单独查看时不显示财务数据
        if user_groups != {"Production"}:
            data["orders_total_amount_by_month"] = self._aggregate(
                active_order_qs,
                Coalesce(F("total_amount"), Decimal("0.0")),
                period="month",
                lookback=12,
            )
            data["orders_total_amount_by_year"] = self._aggregate(
                active_order_qs,
                Coalesce(F("total_amount"), Decimal("0.0")),
                period="year",
                lookback=3,
            )

        return Response(data)
