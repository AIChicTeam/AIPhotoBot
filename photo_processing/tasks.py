from celery import shared_task
import requests
import os
from dotenv import load_dotenv

load_dotenv()

@shared_task
def send_telegram_message(chat_id, text):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=payload)
    return response.json()