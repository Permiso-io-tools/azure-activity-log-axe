"""
Tool Name: Azure Activity Log Axe
Script Name: file_io.py
Author: Nathan Eades
Date: 2024-06-01
Description: Control file i/o across Azure Activity Log Axe.
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

import csv
import json
from .config import valid_output_types
from .logger import get_logger
from pathlib import Path

file_io_logger = get_logger('file_io')
parent_path = Path(__file__).parent.parent.parent


def write_activity_log_data(activity_log: list[dict], default_filename: str, filepath: Path | None = None, output_type: str = "json"):
    write_to_file: bool = True
    if not filepath:
        # Write to default location
        Path(parent_path).joinpath('output').mkdir(parents=True, exist_ok=True)
        filepath = Path(parent_path).joinpath('output', f'{default_filename}.{output_type}')
    else:
        # Build new path
        if not filepath.parent.exists():
            build_path_responses = ['y', 'n', 'yes', 'no']
            build_path: str = ""
            while build_path not in build_path_responses:
                build_path = input(f'The provided path does not exist: {filepath.parent} \nDo you wish to create it? (y/n): ').lower()
            if build_path == 'y' or build_path == "yes":
                filepath.parent.mkdir(parents=True, exist_ok=True)
            else:
                write_to_file = False

    if write_to_file and activity_log:
        try:
            # Force a correct file type
            if output_type not in valid_output_types:
                file_io_logger.info(f'json or csv are the only valid output types. Defaulting to json.')
                output_type = 'json'
                filepath = update_file_extension(filepath, output_type)
            # Force type to match output file type
            if filepath.suffix != f'.{output_type}':
                filepath = update_file_extension(filepath, output_type)
            with open(filepath, 'w', newline='') as file:
                if output_type == 'json':
                    json.dump(activity_log, file, indent=2)
                elif output_type == 'csv':
                    keys = activity_log[0].keys()
                    csv_writer = csv.DictWriter(file, fieldnames=keys)
                    csv_writer.writeheader()
                    csv_writer.writerows(activity_log)
        except Exception as e:
            file_io_logger.critical(f'Unexpected error: {str(e)}.')
    else:
        if not write_to_file:
            file_io_logger.debug(f'No data was written to file, file path did not exist and was not created.')
        elif not activity_log:
            file_io_logger.debug(f'No data was written to file as the activity log is empty.')


def update_file_extension(filepath: Path, new_extension):
    updated_filepath = filepath.with_suffix('.' + new_extension)
    return updated_filepath
