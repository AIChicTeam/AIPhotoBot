from django.db import models

class UserPhoto(models.Model):
    user_id = models.BigIntegerField()
    file_id = models.CharField(max_length=255)
    file_unique_id = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to='user_photos/', null=True, blank=True)

    def __str__(self):
        return f"User {self.user_id}: {self.file_unique_id}"



