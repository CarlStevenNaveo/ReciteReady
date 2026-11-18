
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('INSTRUCTOR', 'Instructor'),
    ]

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    contact_number = models.CharField(
        max_length=20,
        blank=True
    )

    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username
