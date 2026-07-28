from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, verbose_name="شماره تلفن همراه", null=True, blank=True)
    profile_picture = models.ImageField(upload_to="profile_picture/", verbose_name="عکس نمایه", null=True, blank=True)

    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
