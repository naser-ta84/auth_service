from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (RegisterAPIView,
                    VerifyRegistrationOTPAPIView,
                    CustomTokenObtainPairView,
                    RequestOTPAPIView,
                    VerifyOTPAPIView
                    )

urlpatterns = [
    path('register/request/', RegisterAPIView.as_view(), name='register_request'),
    path('register/verify/', VerifyRegistrationOTPAPIView.as_view(), name='register_verify'),

    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('login/otp/request/', RequestOTPAPIView.as_view(), name='login_otp_request'),
    path('login/otp/verify/', VerifyOTPAPIView.as_view(), name='login_otp_verify'),
]
