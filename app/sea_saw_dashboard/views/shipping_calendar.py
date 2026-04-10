from datetime import date, timedelta

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from sea_saw_sales.models import Order
from sea_saw_sales.models.enums import OrderStatusType
from sea_saw_warehouse.models import OutboundOrder


ACTIVE_STATUSES = [OrderStatusType.CONFIRMED]


class ShippingCalendarView(APIView):
    """
    发货日历看板

    GET /api/dashboard/etd-calendar/?year=2026&month=2

    返回：
      - etd.orders_by_date  按 ETD 日期分组的订单列表及发货状态
      - etd.summary         当月 ETD 各状态汇总
      - eta.orders_by_date  按 ETA 日期分组的出库单
      - eta.summary         当月 ETA 各状态汇总
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
    def _get_pipeline(order):
        try:
            return order.pipeline
        except Exception:
            return None

    @staticmethod
    def _get_order_eta(pipeline):
        """从已 prefetch 的 outbound_orders 中取最早的 ETA（非取消）。"""
        if pipeline is None:
            return None
        etas = [
            o.eta
            for o in pipeline.outbound_orders.all()
            if o.eta and o.status != "cancelled"
        ]
        return str(min(etas)) if etas else None

    @staticmethod
    def _determine_shipping_status(order, pipeline, today):
        """
        判断订单发货状态。
        返回: (status, outbound_date)
        status: on_time | shipped_late | outbound_completed | overdue | pending | no_pipeline
        """
        if pipeline is None:
            return "no_pipeline", None

        if pipeline.status in ("outbound_completed", "completed"):
            completed = [
                o
                for o in pipeline.outbound_orders.all()
                if o.status == "completed" and o.outbound_date
            ]
            if not completed:
                return "outbound_completed", None
            latest_date = max(o.outbound_date for o in completed)
            status = "on_time" if latest_date <= order.etd else "shipped_late"
            return status, str(latest_date)

        if order.etd < today:
            return "overdue", None
        return "pending", None

    def get(self, request):
        today = date.today()
        user_groups = set(request.user.groups.values_list("name", flat=True))

        year = int(request.query_params.get("year", today.year))
        month = int(request.query_params.get("month", today.month))

        base_qs = self._get_order_queryset(user_groups)

        # ETD 日历数据
        etd_orders = (
            base_qs.filter(
                etd__year=year,
                etd__month=month,
                status__in=ACTIVE_STATUSES,
            )
            .select_related("buyer", "pipeline")
            .prefetch_related("pipeline__outbound_orders")
            .order_by("etd", "order_code")
        )

        orders_by_etd_date: dict = {}
        etd_summary = {
            "total": 0,
            "on_time": 0,
            "shipped_late": 0,
            "outbound_completed": 0,
            "overdue": 0,
            "pending": 0,
            "no_pipeline": 0,
        }

        for order in etd_orders:
            pipeline = self._get_pipeline(order)
            shipping_status, outbound_date = self._determine_shipping_status(
                order, pipeline, today
            )
            orders_by_etd_date.setdefault(str(order.etd), []).append(
                {
                    "order_id": order.id,
                    "order_code": order.order_code,
                    "account_name": order.buyer.account_name if order.buyer else "",
                    "etd": str(order.etd),
                    "eta": self._get_order_eta(pipeline),
                    "order_status": order.status,
                    "pipeline_id": pipeline.id if pipeline else None,
                    "pipeline_code": pipeline.pipeline_code if pipeline else None,
                    "pipeline_status": pipeline.status if pipeline else None,
                    "shipping_status": shipping_status,
                    "outbound_date": outbound_date,
                    "total_amount": (
                        str(order.total_amount) if order.total_amount else "0.00"
                    ),
                }
            )
            etd_summary["total"] += 1
            etd_summary[shipping_status] = etd_summary.get(shipping_status, 0) + 1

        # ETA 日历数据（当月，按 ETA 日期分组）
        eta_outbounds = (
            OutboundOrder.objects.filter(
                eta__year=year,
                eta__month=month,
                pipeline__order__in=base_qs,
            )
            .exclude(status="cancelled")
            .select_related("pipeline__order__buyer", "pipeline")
            .order_by("eta")
        )

        overdue_cutoff = today - timedelta(days=25)
        eta_summary = {"total": 0, "completed": 0, "overdue": 0, "pending": 0}
        orders_by_eta_date: dict = {}

        for ob in eta_outbounds:
            order = ob.pipeline.order
            orders_by_eta_date.setdefault(str(ob.eta), []).append(
                {
                    "order_id": order.id,
                    "order_code": order.order_code,
                    "account_name": order.buyer.account_name if order.buyer else "",
                    "etd": str(order.etd),
                    "eta": str(ob.eta),
                    "outbound_code": ob.outbound_code,
                    "outbound_status": ob.status,
                    "pipeline_id": ob.pipeline.id,
                    "pipeline_code": ob.pipeline.pipeline_code,
                    "pipeline_status": ob.pipeline.status,
                }
            )
            eta_summary["total"] += 1
            if ob.pipeline.status == "completed":
                eta_summary["completed"] += 1
            elif ob.eta <= overdue_cutoff:
                eta_summary["overdue"] += 1
            else:
                eta_summary["pending"] += 1

        return Response(
            {
                "year": year,
                "month": month,
                "etd": {
                    "summary": etd_summary,
                    "orders_by_date": orders_by_etd_date,
                },
                "eta": {
                    "summary": eta_summary,
                    "orders_by_date": orders_by_eta_date,
                },
            }
        )
