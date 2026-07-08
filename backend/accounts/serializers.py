import re

from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User
from .validators import PhoneNumberValidator,validate_illegal_usernames

class RegisterSerializer(serializers.ModelSerializer):

    confirmation_password = serializers.CharField(write_only=True,)

    class Meta:
        model = User
        fields = [
            'username',
            'phone'
            'password',
            'confirmation_password',
        ]
        extra_kwargs = {
            'password': {
                'write_only': True,
            },
            'phone':{
                'required': True,
                'help_text':'09XXXXXXXXX'
            }
        }

    def validate(self, data):
        confirmation_password = data.get('confirmation_password')
        password = data.get('password')

        if password != confirmation_password:
            raise serializers.ValidationError(
                _('رمز عبور با تکرار ان مطابقت ندارد.'),
                code='password_mismatch',
            )

        tmp_user = User(
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name')
        )

        try:
            validate_password(password=password, user=tmp_user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})

        return data

    def create(self, validated_data):
        validated_data.pop('confirmation_password')
        return User.objects.create_user(**validated_data)

class RequestOPTSerializer(serializers.Serializer):

    phone = serializers.CharField(
        validators=[PhoneNumberValidator()],
        max_length=11,
        min_length=11,
        required=True,
    )

    def validate(self, attrs):
        phone = attrs.get('phone')

        if not User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                {'phone': _('کاربری با این شماره تماس یافت نشد. ابتدا ثبت‌نام کنید.')},
                code='user_not_found'
            )

        return attrs

class VerifyOTPSerializer(serializers.Serializer):

    phone = serializers.CharField(
        validators=[PhoneNumberValidator()],
        max_length=11,
        min_length=11,
        required=True,
    )
    code = serializers.CharField(
        max_length=6,
        min_length=6,
        required=True,
        help_text='XXXXXX'
    )

    def validate_code(self, value):
        if not re.match(r'^\d{6}$', value):
            raise serializers.ValidationError(
                _('کد احراز هویت باید شش رقم و فقط عدد باشد.'),
                code='invalid_code_format'
            )
        return value

    def validate(self, attrs):
        phone = attrs.get('phone')

        if not User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError(
                {'phone': _('کاربری با این شماره تماس یافت نشد.')},
                code='user_not_found'
            )

        return attrs

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        if not self.user.is_verified:
            raise serializers.ValidationError(
                _('.حساب کاربری شما هنوز احراز هویت نشده است. لطفا از طریق رمز یکبار مصرف وارد شوید'),
                code='user_not_verified'
            )

        data['username'] = self.user.username
        data['phone'] = self.user.phone
        data['is_verified'] = self.user.is_verified
        data['detail'] = _('ورود با موفقیت انجام شد.')

        return data