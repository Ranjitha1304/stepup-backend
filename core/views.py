from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import re

from .models import Banner, TrendingItem, Product, Color, Size, Cart, CartItem
from .serializers import (
    BannerSerializer, TrendingItemSerializer, 
    ProductListSerializer, ProductDetailSerializer,
    ColorSerializer, SizeSerializer,
    CartSerializer, CartItemSerializer
)

# --- Banner ---
class BannerViewSet(viewsets.ModelViewSet):
    queryset = Banner.objects.all().order_by("-created_at")
    serializer_class = BannerSerializer

# --- Trending Items ---
class TrendingItemViewSet(viewsets.ModelViewSet):
    queryset = TrendingItem.objects.all()
    serializer_class = TrendingItemSerializer

# --- Contact Form ---
EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
NAME_REGEX = re.compile(r'^[A-Za-z\s]{3,20}$')
PHONE_REGEX = re.compile(r'^\d{10}$')

@csrf_exempt
@api_view(['POST'])
def contact_submit(request):
    data = request.data
    name = (data.get('name') or "").strip()
    email = (data.get('email') or "").strip()
    phone = (data.get('phone') or "").strip()
    message = (data.get('message') or "").strip()

    if not NAME_REGEX.match(name):
        return Response({'error': 'Name must be 3-20 letters.'}, status=400)
    if not EMAIL_REGEX.match(email):
        return Response({'error': 'Invalid email address.'}, status=400)
    if not PHONE_REGEX.match(phone):
        return Response({'error': 'Phone must be exactly 10 digits.'}, status=400)
    if len(message) < 10:
        return Response({'error': 'Message must be at least 10 characters.'}, status=400)

    subject = f"Contact form: {name}"
    body = f"New contact form submission\n\nName: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}\n"

    try:
        send_mail(subject, body, settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER], fail_silently=False)
    except Exception as exc:
        return Response({'error': 'Failed to send email.', 'details': str(exc)}, status=500)

    return Response({'success': 'Message sent'})

# --- User Registration ---
from rest_framework.serializers import ModelSerializer

class RegisterSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"]
        )
        # create cart automatically for user
        Cart.objects.create(user=user)
        return user

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

# --- Products ---
class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all().order_by("-created_at")
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

# --- Cart APIs ---
def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_count(request):
    cart = get_user_cart(request.user)
    total_qty = sum([item.quantity for item in cart.items.all()])
    return Response({'count': total_qty})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_detail(request):
    cart = get_user_cart(request.user)
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_add_item(request):
    """
    Expects JSON:
    {
        "product_id": int,
        "size_id": int,
        "color_id": int,
        "quantity": int
    }
    """
    user = request.user
    cart = get_user_cart(user)
    data = request.data
    product_id = data.get("product_id")
    size_id = data.get("size_id")
    color_id = data.get("color_id")
    quantity = int(data.get("quantity", 1))

    if not (product_id and size_id and color_id):
        return Response({"error": "Product, size, and color are required"}, status=400)

    product = get_object_or_404(Product, pk=product_id)
    size = get_object_or_404(Size, pk=size_id)
    color = get_object_or_404(Color, pk=color_id)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, size=size, color=color,
        defaults={'quantity': quantity}
    )
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cart_update_item(request, item_id):
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    quantity = int(request.data.get("quantity", cart_item.quantity))
    size_id = request.data.get("size_id")
    color_id = request.data.get("color_id")

    if size_id:
        size = get_object_or_404(Size, pk=size_id)
        cart_item.size = size
    if color_id:
        color = get_object_or_404(Color, pk=color_id)
        cart_item.color = color

    if quantity < 1:
        return Response({"error": "Quantity must be at least 1"}, status=400)
    cart_item.quantity = quantity
    cart_item.save()
    serializer = CartItemSerializer(cart_item, context={'request': request})
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def cart_remove_item(request, item_id):
    """
    Remove a cart item by ID in URL
    """
    cart_item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    cart_item.delete()
    return Response({"success": True})



from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, generics
from .serializers import OrderSerializer
from .models import Order

class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Expected payload:
        {
          "total_price": "2799.00",
          "shipping_address": { ... },
          "items": [{ product_id, product_name, sub_name, main_image_url, unit_price, quantity, size, color }, ...]
        }
        """
        data = request.data.copy()
        data["user"] = request.user.id
        serializer = OrderSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            order = serializer.save()
            return Response({"order_number": order.order_number, "id": order.id}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOrdersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by("-created_at")


class TrackOrdersView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderSerializer

    def get_queryset(self):
        # return orders not delivered (current tracking)
        return Order.objects.filter(user=self.request.user).exclude(status="Delivered").order_by("-created_at")
