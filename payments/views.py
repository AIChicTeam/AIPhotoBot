# payments/views.py
import stripe
from django.conf import settings
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Payment
from asgiref.sync import async_to_sync
stripe.api_key = settings.STRIPE_SECRET_KEY
import os

# Получаем доменное имя из переменных окружения
DOMAIN_NAME = os.getenv("DOMAIN_NAME", "localhost")
BASE_URL = f"https://{DOMAIN_NAME}"

@csrf_exempt
def create_checkout_session(request):
    telegram_user_id = request.GET.get("telegram_user_id")
    if not telegram_user_id:
        return HttpResponse("Missing telegram_user_id", status=400)

    # Создаем или обновляем запись платежа
    payment, _ = Payment.objects.get_or_create(telegram_user_id=telegram_user_id)
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'Оплата за загрузку фото',
                },
                'unit_amount': 500,  # $10.00, например
            },
            'quantity': 1,
        }],
        mode='payment',
        metadata={'telegram_user_id': telegram_user_id},
        success_url=f"{BASE_URL}/payments/success/?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{BASE_URL}/payments/cancel/",
    )
    
    # Сохраняем session_id для дальнейшей сверки
    payment.stripe_session_id = session.id
    payment.save()
    
    return redirect(session.url, code=303)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Достаём telegram_user_id из metadata
        telegram_user_id = session.get('metadata', {}).get('telegram_user_id')
        if telegram_user_id:
            # Обновляем статус платежа
            try:
                payment = Payment.objects.get(telegram_user_id=telegram_user_id)
                payment.status = 'paid'
                payment.save()
            except Payment.DoesNotExist:
                pass

            # Отправляем сообщение в Telegram
            from bot_api.bot import application
            async_to_sync(application.bot.send_message)(
                chat_id=telegram_user_id,
                text="Оплата прошла успешно! Теперь вы можете загружать фото."
            )

    return HttpResponse(status=200)

def payment_success(request):
    return render(request, 'payments/success.html')

def payment_cancel(request):
    return render(request, 'payments/cancel.html')
