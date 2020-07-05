from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("thanks/", views.thanks, name="thanks"),
    path("payments/", views.payments, name="payments"),
    path("payments/success", views.payment_success, name="payments-success"),
    path("payments/cancelled", views.payment_cancel, name="payments-cancelled"),
    path("payments/change", views.payment_change, name="payments-change"),
]
