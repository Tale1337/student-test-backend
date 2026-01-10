from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group



# 1. Менеджер юзеров
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен!')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(email, password, **extra_fields)


# 2. Модель пользователя
class CustomUser(AbstractUser):
    username = None
    email = models.EmailField('Email address', unique=True)

    ROLES = (
        ('student', 'Стажёр'),
        ('employer', 'Работодатель'),
        ('admin', 'Администратор'),
    )

    role = models.CharField(max_length=20, choices=ROLES, default='student')

    second_name = models.CharField(max_length=150, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def save(self, *args, **kwargs):

        # 1. Логика пропуска (is_staff)
        if self.role == 'admin':
            self.is_staff = True
        elif not self.is_superuser:
            self.is_staff = False

        super().save(*args, **kwargs)

        # 2. Логика прав (Группа)
        if self.role == 'admin':
            try:
                group = Group.objects.get(name='Managers')
                self.groups.add(group)
            except Group.DoesNotExist:
                pass

        elif not self.is_superuser:
            try:
                group = Group.objects.get(name='Managers')
                self.groups.remove(group)
            except Group.DoesNotExist:
                pass