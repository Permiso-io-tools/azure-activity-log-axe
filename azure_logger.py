import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


FORMATTER = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
parent_path = Path(__file__).parent


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(file_name: str):
    if not Path(parent_path).joinpath("logging").exists():
        Path(parent_path).joinpath("logging").mkdir()
    file_handler = TimedRotatingFileHandler(Path(parent_path).joinpath("logging", file_name), when='midnight')
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(logger.name))
    logger.propagate = False
    return logger
