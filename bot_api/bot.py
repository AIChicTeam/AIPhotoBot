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


from users.views import (
    get_first_screen,
    get_second_screen,
    get_how_it_works_screen,
    get_invite_friends_screen,
    get_support_screen,
    get_payment_screen
)

from bot_api.models import UserPhoto
from payments.models import Payment

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
application = Application.builder().token(TOKEN).build()

@sync_to_async
def get_payment(chat_id):
    try:
        return Payment.objects.get(telegram_user_id=chat_id)
    except Payment.DoesNotExist:
        return None

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

async def start_command(update: Update, context):
    text, reply_markup = get_first_screen()
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
        payment_url = f"https://7241-185-75-238-49.ngrok-free.app/payments/create-checkout-session/?telegram_user_id={chat_id}"
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
        await query.message.reply_text("Now you know how it works! Let's move on...")

    elif data == "go_back":
        text, reply_markup = get_second_screen()
        await query.message.reply_text(text=text, reply_markup=reply_markup)

    elif data == "upload_photos":
        chat_id = query.message.chat_id
        payment = await get_payment(chat_id)
        if not payment or payment.status != 'paid':
            payment_url = f"https://7241-185-75-238-49.ngrok-free.app/payments/create-checkout-session/?telegram_user_id={chat_id}"
            keyboard = [[InlineKeyboardButton("Pay now", url=payment_url)]]
            await query.message.reply_text(
                "Please pay before uploading photos:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.reply_text("Great! Send me 10 photos for AI processing.")

    elif data == "invite_friends":
        text = get_invite_friends_screen()
        await query.message.reply_text(text)

    elif data == "support":
        text = get_support_screen()
        await query.message.reply_text(text)

    else:
        await query.message.reply_text("Unknown action.")

async def handle_photo(update: Update, context):
    user_id = update.message.chat_id

    # Проверяем, оплачен ли платеж
    payment = await get_payment(user_id)
    if not payment or payment.status != 'paid':
        await update.message.reply_text("Для загрузки фото сначала необходимо оплатить.")
        return

    # Проверяем, сколько фото уже загружено
    current_count = await count_photos(user_id)
    if current_count >= 10:
        await update.message.reply_text("Вы уже загрузили максимальное количество фотографий (10).")
        return

    # Извлекаем самое большое фото из списка
    photo_sizes = update.message.photo
    largest_photo = max(photo_sizes, key=lambda p: p.file_size)
    file_id = largest_photo.file_id
    file_unique_id = largest_photo.file_unique_id

    if await exists_photo(user_id, file_unique_id):
        await update.message.reply_text("⛔ Это фото уже загружено. Попробуйте другое!")
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
        await update.message.reply_text(f"✅ Фото принято! Загружено: {current_count}/10")
    except Exception as e:
        print(f"❌ Ошибка при обработке фото: {e}")
        await update.message.reply_text("❌ Ошибка при обработке фото!")

application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_new_user_handler))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CallbackQueryHandler(button_handler))
