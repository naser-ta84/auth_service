from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin
from django.utils.translation import gettext_lazy as _

from .validators import PhoneNumberValidator,UsernameValidator,validate_illegal_usernames
from .managers import UserManager

class User(AbstractBaseUser,PermissionsMixin):

    username = models.CharField(
        max_length=20,
        unique=True,
        validators=[UsernameValidator(),validate_illegal_usernames],
        db_index=True,
        verbose_name=_('نام کاربری'),
    )
    phone = models.CharField(
        validators=[PhoneNumberValidator()],
        unique=True,
        db_index=True,
        max_length=11,
        verbose_name=_('شماره تماس')
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_('وضعیت احراز هویت')
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('دسترسی ادمین')
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name=_('وضعیت فعالیت')
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاریخ عضویت')
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone']


    class Meta:
        verbose_name=_('کاربر')
        verbose_name_plural=_('کاربران')

    def __str__(self):
        return f'{self.phone} - {self.username}'