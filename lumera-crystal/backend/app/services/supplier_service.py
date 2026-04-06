from datetime import datetime


class SupplierService:
    """Mock external supplier API integration."""

    def request_restock(self, *, product_id: int, quantity: int) -> dict:
        return {
            "accepted": True,
            "external_ref": f"SUP-{product_id}-{int(datetime.utcnow().timestamp())}",
            "message": f"restock accepted for product={product_id}, quantity={quantity}",
        }
