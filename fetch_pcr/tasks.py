import logging

from celery import shared_task

from fetch_pcr.utils import find_pcr

logger = logging.getLogger("pcr_logger")


@shared_task
def fetch_pcr_data():
    logger.info("PCR fetching Starting...")
    find_pcr()
