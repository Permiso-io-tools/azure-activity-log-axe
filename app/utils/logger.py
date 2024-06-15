"""
Tool Name: Azure Activity Log Axe
Script Name: logger.py
Author: Nathan Eades
Date: 2024-06-01
Description: Build and control a custom logging mechanism across Azure Activity Log Axe.
License: Apache License
"""

#   This file is part of Azure Activity Log Axe.
#
#   Copyright 2024 Permiso Security <https://permiso.io>
#         Nathan Eades:
#             - LinkedIn: <@eadesclouddef>
#             - GitHub: <eadesclouddef> or <neades2305>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import logging
from .config import LOG_LEVEL
from rich.logging import RichHandler
from rich.console import Console
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

FORMATTER = logging.Formatter('[!] %(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
parent_path = Path(__file__).parent.parent.parent
log_level_types = {10, 20, 30, 40, 50}  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"


def get_logger(name: str, log_level: int = LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)

    if log_level not in log_level_types:
        logger.setLevel(logging.CRITICAL)
    else:
        logger.setLevel(log_level)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(logger.name))
    logger.propagate = False

    return logger


def get_console_handler():
    console_handler = RichHandler(console=Console(), show_time=False)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(file_name: str):
    Path(parent_path).joinpath("logging").mkdir(parents=True, exist_ok=True)
    file_handler = TimedRotatingFileHandler(Path(parent_path).joinpath("logging", file_name), when='midnight')
    file_handler.setFormatter(FORMATTER)
    return file_handler
