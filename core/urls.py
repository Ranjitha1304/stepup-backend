from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .views import (
    BannerViewSet,
    TrendingItemViewSet,
    RegisterView,
    ProductViewSet,
    cart_count,
    cart_detail,
    cart_add_item,
    cart_update_item,
    cart_remove_item,
    contact_submit,
    CheckoutView, UserOrdersView, TrackOrdersView
)

# Router for banners
router = DefaultRouter()
router.register(r'banners', BannerViewSet)
router.register(r'trending', TrendingItemViewSet, basename='trending')
router.register(r'products', ProductViewSet, basename='products')

urlpatterns = [
    # Cart endpoints
    path("cart/", cart_detail, name="cart-detail"),
    path("cart/count/", cart_count, name="cart-count"),
    path("cart/add/", cart_add_item, name="cart-add"),
    path("cart/update/<int:item_id>/", cart_update_item, name="cart-update"),
    path("cart/remove/<int:item_id>/", cart_remove_item, name="cart-remove"),

    # Contact
    path('contact/', contact_submit, name="contact"),

    # Auth
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", UserOrdersView.as_view(), name="user_orders"),
    path("track-orders/", TrackOrdersView.as_view(), name="track_orders"),

    # Router URLs
    path('', include(router.urls)),
]

urlpatterns += router.urls
