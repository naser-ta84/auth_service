from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema,OpenApiResponse

import secrets

from .serializers import RegisterSerializer,VerifyOTPSerializer,CustomTokenObtainPairSerializer,RequestOPTSerializer
from .throttle_classes import OTPRequestThrottle, OTPVerifyThrottle
from .tasks import send_otp_task
from .models import User

class RegisterAPIView(APIView):

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]

    @extend_schema(
        summary="درخواست ثبت‌نام اولیه کاربر",
        description="کاربر اطلاعات اولیه (یوزرنیم، تلفن، پسورد) را ارسال کرده و اکانت غیرفعال ساخته می‌شود. سپس کد OTP صادر و پیامک می‌شود.",
        request=RegisterSerializer,
        responses={
            200: OpenApiResponse(
                description="ثبت‌نام اولیه موفق؛ کد تایید پیامک شد.",
                examples=[{"detail": "کد احراز هویت با موفقیت ارسال شد"}]
            ),
            400: OpenApiResponse(
                description="خطا در اعتبارسنجی داده‌ها (فرمت شماره، یوزرنیم تکراری یا عدم تطابق پسورد)")
        }
    )
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

    @extend_schema(
        summary="تایید کد پیامکی ثبت‌نام",
        description="بررسی کد ارسال شده برای فعال‌سازی نهایی حساب کاربری تازه ساخته شده. در صورت موفقیت، توکن‌های JWT صادر می‌شوند.",
        request=VerifyOTPSerializer,
        responses={
            201: OpenApiResponse(
                description="حساب کاربری با موفقیت فعال شد و توکن‌ها صادر گردیدند.",
                examples=[{
                    "status": "success",
                    "detail": "ثبت نام و احراز هویت با موفقیت انجام شد",
                    "tokens": {"refresh": "string", "access": "string"}
                }]
            ),
            400: OpenApiResponse(description="کد منقضی شده یا اشتباه وارد شده است."),
            404: OpenApiResponse(description="کاربری با این شماره یافت نشد.")
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        input_code = serializer.validated_data.get('code')
        phone = serializer.validated_data.get('phone')
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

    @extend_schema(
        summary="ورود معمولی (نام کاربری و رمز عبور)",
        description="احراز هویت استاندارد با استفاده از نام کاربری و پسورد. در صورت صحت اطلاعات و تایید بودن اکانت، توکن و اطلاعات کاربر بازگردانده می‌شود.",
        responses={
            200: OpenApiResponse(
                description="ورود موفقیت‌آمیز.",
                examples=[{
                    "refresh": "string",
                    "access": "string",
                    "username": "naser",
                    "phone": "09130000000",
                    "is_verified": True,
                    "detail": "ورود با موفقیت انجام شد."
                }]
            ),
            400: OpenApiResponse(description="رمز عبور اشتباه است یا حساب کاربری تایید نشده (is_verified=False) است.")
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class RequestOTPAPIView(APIView):

    permission_classes = [AllowAny]
    throttle_classes = [OTPRequestThrottle]
    serializer_class = RequestOPTSerializer

    @extend_schema(
        summary="درخواست کد ورود یک‌بار مصرف (OTP)",
        description="ارسال شماره تماس کاربر ثبت‌نام شده جهت دریافت کد پیامکی لاگین.",
        request=RequestOPTSerializer,
        responses={
            200: OpenApiResponse(
                description="کد یک‌بار مصرف تولید و پیامک شد.",
                examples=[{"detail": "کد یک بار مصرف با موفقیت ارسال شد."}]
            ),
            400: OpenApiResponse(description="کاربری با این شماره وجود ندارد یا فرمت شماره اشتباه است.")
        }
    )
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

    @extend_schema(
        summary="تایید کد OTP و لاگین کاربر",
        description="بررسی کد یک‌بار مصرف لاگین. اگر کاربر قبلاً مرحله فعال‌سازی ثبت‌نام را کامل نکرده بود، در این مرحله حسابش خودکار فعال (is_verified=True) می‌شود.",
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="کد صحیح است؛ کاربر لاگین شد.",
                examples=[{
                    "status": "success",
                    "detail": "ورود با موفقیت انجام شد.",
                    "tokens": {"refresh": "string", "access": "string"}
                }]
            ),
            400: OpenApiResponse(description="کد منقضی شده یا اشتباه است.")
        }
    )
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