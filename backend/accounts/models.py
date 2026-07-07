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
        blank=True,
        null=True,
        verbose_name=_('شماره تماس')
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name=_('نام')
    )
    last_name = models.CharField(
        max_length=30,
        verbose_name=_('نام خانوادگی')
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('دسترسی ادمین')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('وضعیت فعالیت')
    )
    date_joined = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاریخ عضویت')
    )

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name','last_name']


    class Meta:
        verbose_name=_('کاربر')
        verbose_name_plural=_('کاربران')

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.username}'