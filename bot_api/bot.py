# bot_api/bot.py
import os
import io
from asgiref.sync import sync_to_async
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image
from django.core.files.base import ContentFile


from users.models import Referral
from users.views import (
    get_first_screen,
    get_second_screen,
    get_how_it_works_screen,
    get_invite_friends_screen,
    get_support_screen,
    get_payment_screen,
    get_upload_instructions_screen,
)

from bot_api.models import UserPhoto
from payments.models import Payment


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(TOKEN).build()
DOMAIN_NAME = os.getenv("DOMAIN_NAME", "localhost")
BASE_URL = f"https://{DOMAIN_NAME}"


@sync_to_async
def get_payment(chat_id):
    try:
        return Payment.objects.get(telegram_user_id=chat_id)
    except Payment.DoesNotExist:
        return None
    
def process_payment(telegram_user_id):
    """
    Проверяем, есть ли оплаченный реферал, и начисляем бонус.
    """
    print(f"🔄 Обрабатываем оплату для {telegram_user_id}...")
    
    payment = Payment.objects.filter(telegram_user_id=telegram_user_id, status="pending").first()
    if not payment:
        print(f"❌ Платёж для {telegram_user_id} не найден или уже обработан.")
        return

    payment.status = "paid"
    payment.save()
    print(f"✅ Платёж для {telegram_user_id} обновлён на 'paid'.")

    # Проверяем, был ли он рефералом
    referral = Referral.objects.filter(referred_user_id=telegram_user_id, is_paid=False).first()
    if referral:
        referral.is_paid = True
        referral.save()
        print(f"✅ Реферал {telegram_user_id} оплачен! Начисляем бонус {referral.user_id}.")

        # Начисляем бонус пригласившему
        referrer_id = referral.user_id
        referrer_payment = Payment.objects.filter(telegram_user_id=referrer_id).first()
        if referrer_payment:
            referrer_payment.status = "bonus"
            referrer_payment.save()
            print(f"🎉 Бонус начислен пригласившему {referrer_id}!")
    else:
        print(f"❌ Пользователь {telegram_user_id} не найден в рефералах.")


@sync_to_async
def count_photos(user_id):
    return UserPhoto.objects.filter(user_id=user_id).count()

@sync_to_async
def exists_photo(user_id, file_unique_id):
    return UserPhoto.objects.filter(user_id=user_id, file_unique_id=file_unique_id).exists()

@sync_to_async
def create_photo(user_id, file_id, file_unique_id, processed_file):
    return UserPhoto.objects.create(
        user_id=user_id,
        file_id=file_id,
        file_unique_id=file_unique_id,
        image=processed_file
    )

@sync_to_async
def register_referral(telegram_user_id, referral_code):

    referral = Referral.objects.filter(referral_code=referral_code, referred_user_id__isnull=True).first()
    if referral and referral.user_id != telegram_user_id:  # Исключаем самоприглашение
        referral.referred_user_id = telegram_user_id
        referral.save()
        print(f"✅ Record referal: {telegram_user_id} from {referral.user_id}")
        return True
    print(f"❌ Can't write referal {telegram_user_id} using code: {referral_code}")
    return False

async def start_command(update: Update, context):
    chat_id = update.message.chat_id
    args = context.args  

    referred = False
    if args and args[0].startswith("ref_"):
        referral_code = args[0][4:]
        referred = await register_referral(chat_id, referral_code)

    text, reply_markup = get_first_screen()
    if referred:
        await update.message.reply_text("You joined via a referral link! 🎉")

    await update.message.reply_text(text=text, reply_markup=reply_markup)

async def fallback_new_user_handler(update: Update, context):
    chat_id = update.message.chat_id
    payment = await get_payment(chat_id)
    if payment is None:
        text, reply_markup = get_first_screen()
        await update.message.reply_text(text=text, reply_markup=reply_markup)
    else:
        await update.message.reply_text("Hello! How can I help you?")

async def button_handler(update: Update, context):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "go_to_second_screen":
        text, reply_markup = get_second_screen()
        await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "pay":
        text, reply_markup = get_payment_screen()
        await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "bank_cards":
        chat_id = query.message.chat_id
        payment_url = f"{BASE_URL}/payments/create-checkout-session/?telegram_user_id={chat_id}"
        keyboard = [[InlineKeyboardButton("Pay now (Stripe)", url=payment_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "Click the button below to pay with Stripe.",
            reply_markup=reply_markup
        )

    elif data == "how_it_works":
        text, reply_markup = get_how_it_works_screen()
        await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "how_it_works_next":
        text, reply_markup = get_payment_screen()
        await query.message.reply_text(text=text, reply_markup=reply_markup)


    elif data == "go_back":
        text, reply_markup = get_second_screen()
        await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "upload_photos":
        chat_id = query.message.chat_id
        payment = await get_payment(chat_id)
        if not payment or payment.status != 'paid':
            # Если НЕ оплачено, показываем окно с оплатой
            payment_url = f"{BASE_URL}/payments/create-checkout-session/?telegram_user_id={chat_id}"
            keyboard = [[InlineKeyboardButton("Pay now", url=payment_url)]]
            await query.message.reply_text(
                "Please pay before uploading photos:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # Если оплачено, показываем инструкцию

            text, reply_markup = get_upload_instructions_screen()
            await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "invite_friends":
        chat_id = query.message.chat_id
        text, reply_markup = await get_invite_friends_screen(chat_id)
        await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "support":
        text = get_support_screen()
        await query.message.reply_text(text)

    else:
        await query.message.reply_text("Unknown action.")


async def handle_photo(update: Update, context):
    user_id = update.message.chat_id
    payment = await get_payment(user_id)
    if not payment or payment.status != 'paid':
        await update.message.reply_text("Please pay before uploading photos.")
        return

    current_count = await count_photos(user_id)
    if current_count >= 10:
        # Проверяем, уведомляли ли уже пользователя о превышении лимита
        if not context.user_data.get("max_photos_notified", False):
            context.user_data["max_photos_notified"] = True
            await update.message.reply_text("You have already uploaded the maximum of 10 photos.")
        return

    # Извлекаем самое большое фото из списка
    photo_sizes = update.message.photo
    largest_photo = max(photo_sizes, key=lambda p: p.file_size)
    file_id = largest_photo.file_id
    file_unique_id = largest_photo.file_unique_id

    if await exists_photo(user_id, file_unique_id):
        await update.message.reply_text("⛔ This photo is already uploaded, try another!")
        return

    try:
        # Скачиваем файл с серверов Telegram
        telegram_file = await context.bot.get_file(file_id)
        file_bytes = io.BytesIO()
        await telegram_file.download_to_memory(out=file_bytes)
        file_bytes.seek(0)

        # Обработка изображения через Pillow
        image = Image.open(file_bytes)
        if image.mode != "RGB":
            image = image.convert("RGB")

        width, height = image.size
        if width >= 1024 and height >= 1024:
            left = (width - 1024) // 2
            top = (height - 1024) // 2
            right = left + 1024
            bottom = top + 1024
            image_cropped = image.crop((left, top, right, bottom))
        else:
            image_cropped = image.resize((1024, 1024), resample=Image.LANCZOS)

        output_buffer = io.BytesIO()
        image_cropped.save(output_buffer, format="JPEG", quality=95)
        output_buffer.seek(0)
        processed_file = ContentFile(output_buffer.read(), name=f"{file_unique_id}.jpg")

        await create_photo(user_id, file_id, file_unique_id, processed_file)
        current_count += 1
        await update.message.reply_text(f"✅ Photo accepted! Uploaded: {current_count}/10")
    except Exception as e:
        print(f"❌ Error processing photo: {e}")
        await update.message.reply_text("❌ Error processing photo!")
        return


application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_new_user_handler))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CallbackQueryHandler(button_handler))
