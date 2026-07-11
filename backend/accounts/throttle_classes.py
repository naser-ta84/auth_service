from rest_framework.throttling import AnonRateThrottle

class OTPRequestThrottle(AnonRateThrottle):
    scope = 'otp_request'

class OTPVerifyThrottle(AnonRateThrottle):
    scope = 'otp_verify'