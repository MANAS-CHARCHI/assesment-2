from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils.translation import gettext as _
from datetime import date
import uuid

class UserManager(BaseUserManager):
    use_in_migrations = True
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email instead of a username."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with all permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)

class UserRole(models.TextChoices):
    CLIENT = 'CLIENT', 'Client'
    INSTRUCTOR = 'INSTRUCTOR', 'Instructor'
    ADMIN = 'ADMIN', 'Admin'

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CLIENT)
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    DOB=models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone_number=models.CharField(max_length=15)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login=models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    def save(self, *args, **kwargs):
        # Auto-calculate age if DOB is provided
        if self.DOB:
            today = date.today()
            self.age = today.year - self.DOB.year - ((today.month, today.day) < (self.DOB.month, self.DOB.day))
        super().save(*args, **kwargs)
    
class PasswordReset(models.Model):
    email = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-created_at']

class ActivateAccount(models.Model):
    email = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
   