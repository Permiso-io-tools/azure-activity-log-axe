"""
Tool Name: Azure Activity Log Axe
Script Name: azure_axe_key.py
Author: Nathan Eades
Date: 2024-06-01
Description: Build the axeKey for the data processor.
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

import hashlib
from app.utils.logger import get_logger

axe_key_logger = get_logger('azure_axe_key')

def get_axe_key(cor_id: str | None, operation_name: str | None, resource_id: str | None) -> str | None:
    if cor_id and operation_name and resource_id:
        try:
            cor_id = cor_id.lower()
            operation_name = operation_name.lower()
            resource_id = resource_id.lower()

            return hashlib.md5((f'{cor_id}:{operation_name}:{resource_id}').encode()).hexdigest()
        except Exception as e:
            axe_key_logger.error(f'Axe key creation failure: {e}')

    # Missing data
    axe_key_logger.critical(f'Missing data, key cannot be created.')