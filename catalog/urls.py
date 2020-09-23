from django.urls import path
from .views import (
    HomeView,
    CheckoutView,
    ProductDetail,
    OrderSummaryView,
    PaymentView,
    CouponView,
    payment_complete,
    add_to_cart,
    remove_from_cart,
    remove_single_from_cart
)


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('payment-complete', payment_complete, name="payment_complete"),
    path('add-coupon', CouponView.as_view(), name="add_coupon"),
    path('payment-complete', payment_complete, name="payment_complete"),
    path('add-to-cart/<slug>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('remove-single-from-cart/<slug>/',
         remove_single_from_cart, name='remove_single_from_cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('order-summary/', OrderSummaryView.as_view(), name='order_summary'),
    path('product/<slug>/', ProductDetail.as_view(), name='product'),
]
