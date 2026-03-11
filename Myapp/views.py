from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .cart import Cart
from .forms import CheckoutForm
from .models import Category, Order, OrderItem, Product

#The AI code
from django.http import JsonResponse
from openai import OpenAI

client = OpenAI()

def ai_assistant(request):
    user_message = request.GET.get("message")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You are a helpful boutique shopping assistant."},
            {"role":"user","content":user_message}
        ]
    )

    reply = response.choices[0].message.content

    return JsonResponse({"reply": reply})


def home(request):
    products = Product.objects.filter(is_active=True).order_by("-created_at")[:4]
    return render(request, "shop/home.html", {"products": products})


def products(request):
    q = (request.GET.get("q") or "").strip()
    category_slug = (request.GET.get("category") or "").strip()

    queryset = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)

    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        queryset = queryset.filter(category=selected_category)

    if q:
        queryset = queryset.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(sku__icontains=q))

    return render(
        request,
        "shop/products.html",
        {
            "products": queryset,
            "q": q,
            "categories": categories,
            "selected_category": selected_category,
        },
    )


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)

    if request.method == "POST":
        cart = Cart(request)
        if product.stock <= 0:
            messages.error(request, "This item is currently out of stock.")
        else:
            cart.add(product.id, 1)
            messages.success(request, f"Added {product.name} to your cart.")
        return redirect("cart")

    return render(request, "shop/product_detail.html", {"product": product})


def cart_detail(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart_items": cart.items(), "cart_total": cart.total()})


def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    cart = Cart(request)
    if product.stock <= 0:
        messages.error(request, "This item is currently out of stock.")
    else:
        cart.add(product.id, 1)
        messages.success(request, f"Added {product.name} to your cart.")
    return redirect("cart")


def cart_remove(request, pk):
    cart = Cart(request)
    cart.remove(pk)
    return redirect("cart")


@transaction.atomic
def checkout(request):
    cart = Cart(request)
    cart_items = cart.items()
    if not cart_items:
        messages.info(request, "Your cart is empty.")
        return redirect("products")

    initial = {}
    if request.user.is_authenticated:
        if request.user.email:
            initial["email"] = request.user.email
        initial["full_name"] = request.user.get_full_name() or request.user.username

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Stock validation just before creating the order.
            for row in cart_items:
                product = row["product"]
                if product.stock < row["quantity"]:
                    messages.error(request, f"Not enough stock for {product.name}.")
                    return redirect("cart")

            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                email=form.cleaned_data["email"],
                full_name=form.cleaned_data["full_name"],
                phone=form.cleaned_data["phone"],
                address_line1=form.cleaned_data["address_line1"],
                address_line2=form.cleaned_data["address_line2"],
                city=form.cleaned_data["city"],
                country=form.cleaned_data["country"],
                status="new",
            )

            for row in cart_items:
                product = Product.objects.select_for_update().get(pk=row["product"].pk)
                qty = row["quantity"]
                if product.stock < qty:
                    raise ValueError("Stock changed during checkout")
                product.stock -= qty
                product.save(update_fields=["stock"])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    unit_price=product.price,
                    quantity=qty,
                )

            cart.clear()
            messages.success(request, "Order placed. Thank you.")
            return redirect("order_success", order_id=order.id)
    else:
        form = CheckoutForm(initial=initial)

    return render(
        request,
        "shop/checkout.html",
        {"form": form, "cart_items": cart_items, "cart_total": cart.total()},
    )


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "shop/order_success.html", {"order": order})


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})
