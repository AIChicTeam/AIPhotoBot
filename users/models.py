import uuid
from django.db import models

def generate_referral_code():
    return str(uuid.uuid4())[:8]  # Генерируем 8-символьный уникальный код

class Referral(models.Model):
    user_id = models.BigIntegerField()  # Кто пригласил
    referral_code = models.CharField(max_length=50, unique=True, default=generate_referral_code)  # Код
    referred_user_id = models.BigIntegerField(null=True, blank=True)  # Кого пригласили
    is_paid = models.BooleanField(default=False)  # Оплатил ли реферал

    def __str__(self):
        return f"{self.user_id} → {self.referral_code} ({'Paid' if self.is_paid else 'Pending'})"

    def get_referral_link(self):
        """Генерирует ссылку на бота с реферальным кодом"""
        return f"https://t.me/AIMelnykBot?start=ref_{self.referral_code}"

