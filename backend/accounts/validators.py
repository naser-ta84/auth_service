import re

from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class PhoneNumberValidator(RegexValidator):
    regex = r'^09\d{9}$'
    message = _('شماره تلفن باید با 09 شروع شده و 11 رقم باشد.')

class UsernameValidator(RegexValidator):
    regex = r'^[a-zA-Z0-9][a-zA-Z0-9._-]{3,19}$'
    message = _('نام کاربری باید بین 3 تا 20 کاراکتر و شامل حروف/ارقام/./-/_ باشد.')

def validate_illegal_usernames(value):

    illegal_username = ['admin','root','superuser','support','api','auth','administrator',
                        'ادمین']

    if value.lower() in illegal_username:
        raise ValidationError(
            _('استفاده از نام کاریری مجاز نیست.'),
            code='illegal_username',
        )


class PasswordComplexityValidator:

     def validate(self, password, user=None):

         if not re.search(r'[A-Z]', password):
             raise ValidationError(
                 _('رمز عبور باید شامل حداقل یک حرف بزرگ انگلیسی باشد.'),
                 code='password_no_uppercase_letter',
             )

         if not re.search(r'[a-z]', password):
             raise ValidationError(
                 _('رمز عبور باید شامل حداقل یک حرف کوچک انگلیسی باشد'),
                 code='password_no_lowercase_letter',
             )

         if not re.search(r'[0-9]', password):
             raise ValidationError(
                 _('رمز عبور باید شامل حداقل یک عدد باشد.'),
                 code='password_no_number',
             )

         if not re.search('[!@#$%^&*()":{}|<>_+-]', password):
             raise ValidationError(
                 _('رمز عبور باید شامل حداقل یک کاراکتر خاص همانند ! ، # و ... باشد'),
                 code='password_no_special_character',
             )

     def get_help_text(self):
         return _(
             'رمز عبور باید شامل حروف بزرگ و کوچک انگلیسی ، عدد ، و کاراکتر های خاص باشد.'
         )

class PersonalInfoSimilarityValidator:

    def validate(self, password, user=None):
        if user is None:
            return

        essential_fields = [
            getattr(user, 'username',''),
        ]

        password_lower = password.lower()

        for field in essential_fields:
            if field and len(field) >= 3 :
                field_lower = field.lower()
                if field_lower in password_lower:
                    raise ValidationError(
                        _('رمز عبور نباید شامل نام ، نام خانوادگی یا نام کاربری باشد'),
                        code='password_matches_user_info'
                    )


    def get_help_text(self):
        return _(
            'رمز عبور نباید شامل اطلاعات شخصی شما باشد'
        )