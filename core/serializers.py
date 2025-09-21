from rest_framework import serializers
from .models import Banner, TrendingItem, Product, ProductImage, Color, Size, Cart, CartItem

# --- Banner ---
class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"

# --- TrendingItem ---
class TrendingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendingItem
        fields = "__all__"

# --- Product related ---
class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ("id", "name", "hex")

class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = ("id", "value")

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "image", "order")

class ProductListSerializer(serializers.ModelSerializer):
    colors = ColorSerializer(many=True)
    sizes = SizeSerializer(many=True)
    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "sub_name",
            "price",
            "rating",
            "main_image_url",
            "colors",
            "sizes",
            "category",
        )

    def get_main_image_url(self, obj):
        request = self.context.get("request")
        if obj.main_image:
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return ""

class ProductDetailSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    colors = ColorSerializer(many=True)
    sizes = SizeSerializer(many=True)

    class Meta:
        model = Product
        fields = ("id", "name", "sub_name", "price", "rating", "description", "category", "images", "colors", "sizes", "secure_checkout_image", "size_help_image")

# --- Cart serializers ---
class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    sub_name = serializers.CharField(source="product.sub_name", read_only=True)
    price = serializers.DecimalField(source="product.price", max_digits=10, decimal_places=2, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    size = SizeSerializer(read_only=True)
    color = ColorSerializer(read_only=True)
    available_sizes = SizeSerializer(source="product.sizes", many=True, read_only=True)
    available_colors = ColorSerializer(source="product.colors", many=True, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_name", "sub_name", "price", "main_image_url", "size", "color", "available_sizes", "available_colors", "quantity")

    def get_main_image_url(self, obj):
        if obj.product.main_image:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.product.main_image.url)
            return obj.product.main_image.url
        return ""

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ("id", "user", "items", "total_price")

    def get_total_price(self, obj):
        return sum([item.product.price * item.quantity for item in obj.items.all()])



from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            "product_id",
            "product_name",
            "sub_name",
            "main_image_url",
            "unit_price",
            "quantity",
            "size",
            "color",
        ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "total_price",
            "shipping_address",
            "payment_status",
            "status",
            "created_at",
            "items",
        ]
        read_only_fields = ["id", "order_number", "user", "created_at", "status", "payment_status"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        request = self.context.get("request")
        user = request.user if request else None

        # Default empty dict if missing
        shipping_address = validated_data.pop("shipping_address", {})

        order = Order.objects.create(user=user, shipping_address=shipping_address, **validated_data)

        order_items = []
        for item in items_data:
            order_items.append(OrderItem(order=order, **item))
        OrderItem.objects.bulk_create(order_items)
        return order
