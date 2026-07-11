from celery import shared_task
from logging import getLogger

logger = getLogger(__name__)

@shared_task
def send_otp_task(phone, code):
    logger.info('................')
    logger.info(f'Phone: {phone}')
    logger.info(f'Code: {code}')
    logger.info('................')
