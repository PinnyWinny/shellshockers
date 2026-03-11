from django.core.management.base import BaseCommand
from django.utils.text import slugify

from Myapp.models import Category, Product


class Command(BaseCommand):
    help = "Seed demo categories and products (no images)."

    def handle(self, *args, **options):
        categories = ["Bags", "Accessories", "Ready-to-wear"]
        category_map = {}
        for name in categories:
            category, _ = Category.objects.get_or_create(
                slug=slugify(name), defaults={"name": name, "is_active": True}
            )
            category_map[name] = category

        demo_products = [
            ("Amber Mini Bag", "Bags", "A compact everyday bag in warm tones.", "149.00", 12),
            ("Sienna Tote", "Bags", "A clean-lined tote with strong structure.", "229.00", 8),
            ("Gold Buckle Belt", "Accessories", "A minimal belt with a bright buckle.", "59.00", 25),
            ("Silk Scarf", "Accessories", "Soft sheen, boutique print, easy drape.", "39.00", 30),
            ("Warm Knit Cardigan", "Ready-to-wear", "Lightweight knit layer for evenings.", "89.00", 10),
        ]

        created = 0
        for name, cat, desc, price, stock in demo_products:
            slug = slugify(name)
            product, was_created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "sku": slug.upper().replace("-", "")[:12],
                    "category": category_map[cat],
                    "description": desc,
                    "price": price,
                    "stock": stock,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded demo data. New products: {created}"))
