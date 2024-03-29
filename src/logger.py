import logging
import logging.handlers


# logs etc.
LOGFILE = "log/calendar_python.log"


def create_logger() -> logging.Logger:
    """
    Creates a rotating file_handler logger.

    @return: (logging.Logger) the rotating file handler logger
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOGFILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = create_logger()
