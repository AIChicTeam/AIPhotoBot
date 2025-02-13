import asyncio
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import io
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from bot_api.models import UserPhoto
from PIL import Image
from django.core.files.base import ContentFile

# Получаем токен из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализируем приложение Telegram Bot
application = Application.builder().token(TOKEN).build()


# --- Обработчики ---

# Обработчик команды /start
async def start(update: Update, context):
    print(f"✅ Вызван /start от {update.message.chat_id}")
    await update.message.reply_text(
        "Привет! Загрузи от 2 до 10 фото для AI-обработки!"
    )


# Обработчик получения фотографий
async def handle_photo(update: Update, context):
    user_id = update.message.chat_id

    # Ограничение: не более 10 фотографий
    current_count = await UserPhoto.objects.filter(user_id=user_id).acount()
    if current_count >= 10:
        await update.message.reply_text("Вы уже загрузили максимальное количество фотографий (10).")
        return

    photo_sizes = update.message.photo
    largest_photo = max(photo_sizes, key=lambda p: p.file_size)
    file_id = largest_photo.file_id
    file_unique_id = largest_photo.file_unique_id

    # Проверка на дубликат
    exists = await UserPhoto.objects.filter(user_id=user_id, file_unique_id=file_unique_id).aexists()
    if exists:
        await update.message.reply_text("⛔ Это фото уже загружено. Попробуйте другое!")
        return

    try:
        # Загрузка файла с серверов Telegram
        telegram_file = await context.bot.get_file(file_id)
        file_bytes = io.BytesIO()
        await telegram_file.download_to_memory(out=file_bytes)
        file_bytes.seek(0)

        # Открываем изображение через Pillow
        image = Image.open(file_bytes)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Определяем размеры исходного изображения
        width, height = image.size

        # Если фото больше или равно 1024x1024 – обрезаем центральную область
        if width >= 1024 and height >= 1024:
            left = (width - 1024) // 2
            top = (height - 1024) // 2
            right = left + 1024
            bottom = top + 1024
            image_cropped = image.crop((left, top, right, bottom))
        else:
            # Если меньше, масштабируем с сохранением качества (но помните, что увеличение может привести к потере четкости)
            image_cropped = image.resize((1024, 1024), resample=Image.LANCZOS)

        # Сохраняем обработанное изображение в буфер с высоким качеством JPEG
        output_buffer = io.BytesIO()
        image_cropped.save(output_buffer, format="JPEG", quality=95)
        output_buffer.seek(0)

        processed_file = ContentFile(output_buffer.read(), name=f"{file_unique_id}.jpg")

        await UserPhoto.objects.acreate(
            user_id=user_id,
            file_id=file_id,
            file_unique_id=file_unique_id,
            image=processed_file
        )
        # Увеличиваем счётчик фотографий после сохранения
        current_count += 1
        await update.message.reply_text(f"✅ Фото принято! Загружено: {current_count}/10")
    except Exception as e:
        print(f"❌ Ошибка при обработке фото: {e}")
        await update.message.reply_text("❌ Ошибка при обработке фото!")


# Обработчик нажатия кнопок (CallbackQuery)
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Пожалуйста, загрузите от 2 до 10 фото. Мы не принимаем дубликаты."
    )


# --- Регистрация обработчиков в приложении ---
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
application.add_handler(CallbackQueryHandler(button_handler))
