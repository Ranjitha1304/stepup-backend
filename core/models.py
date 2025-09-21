from django.db import models
from django.contrib.auth.models import User

# --- Banner ---
class Banner(models.Model):
    image = models.ImageField(upload_to="banners/")
    link = models.URLField(blank=True, null=True)  # optional
    created_at = models.DateTimeField(auto_now_add=True)

# --- Trending Items ---
class TrendingItem(models.Model):
    name = models.CharField(max_length=255)
    sub_name = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="trending/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.name

# --- Product related ---
CATEGORY_CHOICES = (
    ("men", "Mens"),
    ("women", "Womens"),
    ("kids", "Kids"),
)

class Color(models.Model):
    name = models.CharField(max_length=50)
    hex = models.CharField(max_length=7, help_text="#rrggbb")

    def __str__(self):
        return f"{self.name} ({self.hex})"

class Size(models.Model):
    value = models.CharField(max_length=10)  # e.g. "41", "L"

    def __str__(self):
        return self.value

class Product(models.Model):
    name = models.CharField(max_length=255)
    main_image = models.ImageField(upload_to="products/", blank=True, null=True)
    sub_name = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=16, choices=CATEGORY_CHOICES)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    secure_checkout_image = models.ImageField(upload_to="secure_images/", blank=True, null=True)
    size_help_image = models.ImageField(upload_to="size_help/", blank=True, null=True)
    colors = models.ManyToManyField(Color, blank=True)
    sizes = models.ManyToManyField(Size, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.product.name} image #{self.order}"

# --- Cart models ---
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.PROTECT)
    color = models.ForeignKey(Color, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'product', 'size', 'color')

    def __str__(self):
        return f"{self.product.name} ({self.size}/{self.color}) x {self.quantity}"


from django.db import models
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ("Pending", "Order Placed"),
        ("Processing", "Order Dispatched"),
        ("Shipped", "Order in Transit"),
        ("Delivered", "Delivered Successfully"),
        ("Cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_number = models.CharField(max_length=64, unique=True, db_index=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_address = models.JSONField()  
    payment_status = models.CharField(max_length=20, default="Pending")
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_number} - {self.user}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            uid = uuid.uuid4().hex[:6].upper()
            self.order_number = f"ORD-{uid}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    sub_name = models.CharField(max_length=255, blank=True, null=True)
    main_image_url = models.CharField(max_length=500, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=64, blank=True, null=True)
    color = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f"{self.product_name} x{self.quantity} ({self.order.order_number})"
