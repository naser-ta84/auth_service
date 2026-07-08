from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

import secrets

from .serializers import RegisterSerializer,VerifyOTPSerializer,CustomTokenObtainPairSerializer,RequestOPTSerializer
from .throttle_classes import OTPRequestThrottle, OTPVerifyThrottle
from .tasks import send_otp_task
from .models import User

class RegisterAPIView(APIView):

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    def post(self, request, *args, **kwargs):

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        cache_key = f'OTP for {user.phone}'
        code = f'{secrets.randbelow(900000)+100000}'

        cache.set(
            key=cache_key,
            value=code,
            timeout=120
        )

        send_otp_task.delay(
            phone=user.phone,
            code=code
        )

        return Response(
            {
                'detail':_('کد احراز هویت با موفقیت ارسال شد')
            },
            status=status.HTTP_200_OK,
        )

class VerifyRegistrationOTPAPIView(APIView):

    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer
    throttle_classes = [OTPVerifyThrottle]

    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        input_code = serializer.data.get('code')
        phone = serializer.data.get('phone')
        cache_key = f'OTP for {phone}'

        cached_code = cache.get(
            key=cache_key
        )

        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response(
                {
                    'detail':_('کاربری با این شماره یافت نشد')
                },
                status=status.HTTP_404_NOT_FOUND
            )


        if not cached_code:

            return Response(
                {
                    'status':'failed',
                    'detail':_('کد احراز هویت منقضی شده است .لطفا مجدد درخواست دهید.')
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if input_code != cached_code:
            return Response(
                {
                    'status':'failed',
                    'detail':_('کد وارد شده با کد ارسال شده مطابقت ندارد')
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(
            key=cache_key
        )

        user.is_verified = True
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'status':'success',
                'detail':_('ثبت نام و احراز هویت با موفقیت انجام شد'),
                'tokens':{
                    'refresh':str(refresh),
                    'access':str(refresh.access_token)
                }
            },
            status=status.HTTP_201_CREATED,
        )

class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [UserRateThrottle]
    serializer_class = CustomTokenObtainPairSerializer

class RequestOTPAPIView(APIView):

    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]
    serializer_class = RequestOPTSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get('phone')

        cache_key = f'OTP for {phone}'
        code = f'{secrets.randbelow(900000) + 100000}'

        cache.set(
            key=cache_key,
            value=code,
            timeout=120
        )

        send_otp_task.delay(
            phone=phone,
            code=code
        )

        return Response(
            {
                'detail':_('کد یک بار مصرف با موفقیت ارسال شد.')
            },
            status=status.HTTP_200_OK,
        )

class VerifyOTPAPIView(APIView):

    permission_classes = [AllowAny]
    throttle_classes = [OTPVerifyThrottle]
    serializer_class = VerifyOTPSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data.get('phone')
        input_code = serializer.validated_data.get('code')

        cache_key = f'OTP for {phone}'

        cached_code = cache.get(
            key=cache_key
        )

        if not cached_code:
            return Response(
                {
                    'status':'failed',
                    'detail':_('کد یک بار مصرف منقضی شده است.')
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if input_code != cached_code:
            return Response(
                {
                    'status':'failed',
                    'detail':_('کد ورودی نامعتبر است.')
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cache.delete(
            key=cache_key
        )

        user = User.objects.filter(phone=phone).first()

        if not user.is_verified:
            user.is_verified = True
            user.is_active = True
            user.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'status':'success',
                'detail':_('ورود با موفقیت انجام شد.'),
                'tokens':{
                    'refresh':str(refresh),
                    'access':str(refresh.access_token)
                }
            },
            status=status.HTTP_200_OK,
        )