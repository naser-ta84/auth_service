from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):

    def _create_user(self, username,phone,password=None, **extra_fields):

        if not username:
            raise ValueError(
                'نام کاربری الزامی است.'
            )

        user = self.model(
            username=username,
            phone=phone,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self,username,phone,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',False)
        extra_fields.setdefault('is_superuser',False)
        extra_fields.setdefault('is_active',True)
        return self._create_user(username,phone,password,**extra_fields)

    def create_superuser(self, username, phone,password=None,**extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active',True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'Superuser must have is_staff=True.'
            )
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Superuser must have is_superuser=True.'
            )

        return self._create_user(username, phone,password,**extra_fields)