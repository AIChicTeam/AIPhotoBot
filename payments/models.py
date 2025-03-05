# payments/models.py
from django.db import models

class Payment(models.Model):
    telegram_user_id = models.BigIntegerField(unique=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, default='pending')  # pending, paid
    created_at = models.DateTimeField(auto_now_add=True)
    star_balance = models.IntegerField(default=0)

    def __str__(self):
        return f"Payment for {self.telegram_user_id}: {self.status}"

