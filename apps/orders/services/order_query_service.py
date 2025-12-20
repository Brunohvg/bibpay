from datetime import datetime, timedelta
from django.db.models import Prefetch

from apps.orders.models import Order
from apps.payments.models import PaymentLink


def list_orders_filtered(params):
    payment_links_qs = PaymentLink.objects.select_related("payment")

    queryset = (
        Order.objects
        .select_related("seller")
        .prefetch_related(
            Prefetch(
                "payment_links",
                queryset=payment_links_qs,
                to_attr="prefetched_payment_links",
            )
        )
        .order_by("-created_at")
    )

    seller_id = params.get("seller")
    date_start = params.get("date_start")
    date_end = params.get("date_end")

    if seller_id and seller_id.isdigit():
        queryset = queryset.filter(seller_id=seller_id)

    if date_start:
        try:
            queryset = queryset.filter(
                created_at__gte=datetime.strptime(date_start, "%Y-%m-%d")
            )
        except ValueError:
            pass

    if date_end:
        try:
            queryset = queryset.filter(
                created_at__lt=datetime.strptime(date_end, "%Y-%m-%d") + timedelta(days=1)
            )
        except ValueError:
            pass

    return queryset
