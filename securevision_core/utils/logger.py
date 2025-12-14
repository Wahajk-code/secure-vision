import logging
import sys
from config import LOG_FILE_PATH

def setup_logger(name=__name__):
    """
    Sets up a logger that logs to both console and a file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Check if handlers are already added to avoid duplicate logs
    if not logger.handlers:
        # Create handlers
        c_handler = logging.StreamHandler(sys.stdout)
        f_handler = logging.FileHandler(LOG_FILE_PATH)

        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(logging.DEBUG)

        # Create formatters and add it to handlers
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger
