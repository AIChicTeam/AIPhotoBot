# bot_api/views.py
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from .bot import application  # Импортируем объект application из bot.py

logger = logging.getLogger(__name__)

@csrf_exempt
async def telegram_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            print(f"📩 Получено обновление: {json.dumps(data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print("❌ Ошибка JSON")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        update = Update.de_json(data, application.bot)
        print(f"📌 Обрабатываем обновление: {update}")

        if not application.running:
            await application.initialize()

        await application.process_update(update)
        return JsonResponse({"status": "ok"})
    else:
        print("❌ Неверный тип запроса")
        return JsonResponse({"error": "Invalid request"}, status=400)
