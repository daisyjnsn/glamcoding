import logging
from logging.handlers import TimedRotatingFileHandler


def setupLogger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler('app.log'),
            TimedRotatingFileHandler(
                filename="app.log",
                when="midnight",
                interval=1,
                backupCount=7,
                encoding="utf-8"
            )
        ]
    )
    logger = logging.getLogger(__name__)
    return logger


logger = setupLogger()