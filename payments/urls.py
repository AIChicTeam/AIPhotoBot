# payments/urls.py
from django.urls import path
from .views import create_checkout_session, payment_success, payment_cancel
from . import views
urlpatterns = [
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('success/', payment_success, name='payment_success'),
    path('cancel/', payment_cancel, name='payment_cancel'),
    path('stripe_webhook/', views.stripe_webhook, name='stripe_webhook'),
]
