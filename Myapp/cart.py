from decimal import Decimal

from .models import Product


class Cart:
    """
    Session-backed cart. Stored as {"product_id": quantity}.
    """

    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session
        self._cart = self.session.get(self.SESSION_KEY, {})

    def add(self, product_id: int, quantity: int = 1):
        product_key = str(product_id)
        current_qty = int(self._cart.get(product_key, 0))
        self._cart[product_key] = max(0, current_qty + int(quantity))
        if self._cart[product_key] == 0:
            self._cart.pop(product_key, None)
        self._save()

    def set(self, product_id: int, quantity: int):
        product_key = str(product_id)
        qty = int(quantity)
        if qty <= 0:
            self._cart.pop(product_key, None)
        else:
            self._cart[product_key] = qty
        self._save()

    def remove(self, product_id: int):
        self._cart.pop(str(product_id), None)
        self._save()

    def clear(self):
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True
        self._cart = {}

    def items(self):
        product_ids = [int(pid) for pid in self._cart.keys()]
        products = Product.objects.filter(id__in=product_ids, is_active=True)
        products_by_id = {p.id: p for p in products}

        result = []
        for pid_str, qty in self._cart.items():
            product = products_by_id.get(int(pid_str))
            if not product:
                continue
            qty_int = int(qty)
            unit_price = product.price
            result.append(
                {
                    "product": product,
                    "quantity": qty_int,
                    "unit_price": unit_price,
                    "line_total": (Decimal(unit_price) * qty_int),
                }
            )
        return result

    def count(self):
        return sum(int(qty) for qty in self._cart.values())

    def total(self):
        total = Decimal("0.00")
        for row in self.items():
            total += row["line_total"]
        return total

    def _save(self):
        self.session[self.SESSION_KEY] = self._cart
        self.session.modified = True
