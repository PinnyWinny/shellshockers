from .cart import Cart


def cart_item_count(request):
    try:
        return {"cart_item_count": Cart(request).count()}
    except Exception:
        # Avoid breaking template rendering if sessions aren't available.
        return {"cart_item_count": 0}
