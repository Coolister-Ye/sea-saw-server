from datetime import date, timedelta

from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sea_saw_pipeline.models import Pipeline
from sea_saw_sales.models import Order
from sea_saw_sales.models.enums import OrderStatusType


ACTIVE_STATUSES = [OrderStatusType.CONFIRMED]

# Pipeline 状态到中文标签映射
PIPELINE_STATUS_LABELS = {
    "order_confirmed": "已确认",
    "in_purchase": "采购中",
    "purchase_completed": "采购完成",
    "in_production": "生产中",
    "production_completed": "生产完成",
    "in_purchase_and_production": "采购+生产",
    "purchase_and_production_completed": "采购+生产完成",
    "in_outbound": "发货中",
    "outbound_completed": "发货完成",
    "issue_reported": "异常上报",
}

# 预警清单：已处于安全阶段的不纳入预警
SAFE_PIPELINE_STATUSES = [
    "in_outbound",
    "outbound_completed",
    "completed",
    "cancelled",
]

# Pipeline 分布图：排除草稿/已结束状态
DISTRIBUTION_EXCLUDE_STATUSES = ["draft", "completed", "cancelled"]


class ETDCalendarView(APIView):
    """
    ETD 日历及进度看板

    GET /api/dashboard/etd-calendar/?year=2026&month=2

    一次返回三块数据：
      1. orders_by_date    - 按 ETD 日期分组的订单列表及发货状态
      2. warning_list      - ETD 在 7 天内但尚未进入发货阶段的风险订单
      3. pipeline_distribution - 当前活跃 Pipeline 按阶段分布
    """

    permission_classes = [IsAuthenticated]

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
    def _determine_shipping_status(order, today):
        """
        通过已 prefetch 的 pipeline.outbound_orders 判断发货状态。
        返回值: on_time | shipped_late | overdue | pending | no_pipeline
        """
        try:
            pipeline = order.pipeline
        except Exception:
            return "no_pipeline", None

        if pipeline is None:
            return "no_pipeline", None

        outbounds = list(pipeline.outbound_orders.all())
        completed = [o for o in outbounds if o.status == "completed" and o.outbound_date]

        if completed:
            earliest_date = min(o.outbound_date for o in completed)
            if earliest_date <= order.etd:
                return "on_time", str(earliest_date)
            return "shipped_late", str(earliest_date)

        if order.etd < today:
            return "overdue", None
        return "pending", None

    def get(self, request):
        today = date.today()
        user_groups = set(request.user.groups.values_list("name", flat=True))

        year = int(request.query_params.get("year", today.year))
        month = int(request.query_params.get("month", today.month))

        base_qs = self._get_order_queryset(user_groups)

        # ── 1. ETD 日历数据 ──────────────────────────────────────────────
        calendar_orders = (
            base_qs.filter(
                etd__year=year,
                etd__month=month,
                status__in=ACTIVE_STATUSES,
            )
            .select_related("account", "pipeline")
            .prefetch_related("pipeline__outbound_orders")
            .order_by("etd", "order_code")
        )

        orders_by_date: dict = {}
        summary = {"total": 0, "on_time": 0, "shipped_late": 0, "pending": 0, "overdue": 0, "no_pipeline": 0}

        for order in calendar_orders:
            shipping_status, outbound_date = self._determine_shipping_status(order, today)
            date_key = str(order.etd)

            try:
                pipeline = order.pipeline
                pipeline_id = pipeline.id if pipeline else None
                pipeline_code = pipeline.pipeline_code if pipeline else None
                pipeline_status = pipeline.status if pipeline else None
            except Exception:
                pipeline_id = None
                pipeline_code = None
                pipeline_status = None

            entry = {
                "order_id": order.id,
                "order_code": order.order_code,
                "account_name": order.account.account_name if order.account else "",
                "etd": str(order.etd),
                "order_status": order.status,
                "pipeline_id": pipeline_id,
                "pipeline_code": pipeline_code,
                "pipeline_status": pipeline_status,
                "shipping_status": shipping_status,
                "outbound_date": outbound_date,
                "total_amount": str(order.total_amount) if order.total_amount else "0.00",
            }

            orders_by_date.setdefault(date_key, []).append(entry)
            summary["total"] += 1
            summary[shipping_status] = summary.get(shipping_status, 0) + 1

        # ── 2. 预警清单（不限月份，独立查询）────────────────────────────
        warning_orders = (
            base_qs.filter(
                etd__gte=today,
                etd__lte=today + timedelta(days=7),
                status__in=ACTIVE_STATUSES,
            )
            .exclude(pipeline__status__in=SAFE_PIPELINE_STATUSES)
            .select_related("account", "pipeline")
            .prefetch_related("pipeline__outbound_orders")
            .order_by("etd")
        )

        warning_list = []
        for order in warning_orders:
            shipping_status, _ = self._determine_shipping_status(order, today)
            if shipping_status in ("on_time", "shipped_late"):
                continue  # 已完成发货的排除

            try:
                pipeline = order.pipeline
                pipeline_id = pipeline.id if pipeline else None
                pipeline_status = pipeline.status if pipeline else None
            except Exception:
                pipeline_id = None
                pipeline_status = None

            days_until_etd = (order.etd - today).days

            warning_list.append({
                "order_id": order.id,
                "order_code": order.order_code,
                "account_name": order.account.account_name if order.account else "",
                "etd": str(order.etd),
                "pipeline_id": pipeline_id,
                "pipeline_status": pipeline_status,
                "days_until_etd": days_until_etd,
            })

        # ── 3. Pipeline 阶段分布 ─────────────────────────────────────────
        distribution_qs = (
            Pipeline.objects.filter(deleted__isnull=True)
            .exclude(status__in=DISTRIBUTION_EXCLUDE_STATUSES)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        pipeline_distribution = [
            {
                "status": row["status"],
                "label": PIPELINE_STATUS_LABELS.get(row["status"], row["status"]),
                "count": row["count"],
            }
            for row in distribution_qs
        ]

        return Response(
            {
                "year": year,
                "month": month,
                "orders_by_date": orders_by_date,
                "summary": summary,
                "warning_list": warning_list,
                "pipeline_distribution": pipeline_distribution,
            }
        )
