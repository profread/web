from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("payment/setup/", views.payment_setup, name="payment-setup"),
    path("payment/success/", views.payment_success, name="payment-success"),
    path("payment/cancel/", views.payment_cancel, name="payment-cancel"),
]
