from django.contrib import admin
from .models import Banner, TrendingItem


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("created_at",)



@admin.register(TrendingItem)
class TrendingItemAdmin(admin.ModelAdmin):
    list_display = ("name", "sub_name", "price", "created_at")
    search_fields = ("name", "sub_name")


from .models import Product, ProductImage, Color, Size

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 6

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "rating", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "sub_name")
    inlines = [ProductImageInline]
    filter_horizontal = ("colors", "sizes")

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex")

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("value",)




# admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "sub_name", "main_image_url", "unit_price", "quantity", "size", "color")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "user", "status", "total_price", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("order_number", "user__username")
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "created_at", "updated_at", "total_price", "shipping_address")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("product_name", "order", "quantity", "unit_price")
    search_fields = ("product_name", "order__order_number")
