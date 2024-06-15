"""
Tool Name: Azure Activity Log Axe
Script Name: log_getters.py
Author: Nathan Eades
Date: 2024-06-01
Description: Pull log data from the Azure Monitor Insights endpoint.
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

import requests
from .auth import AzureMonitorAuth
from .logger import get_logger
from datetime import datetime
from datetime import timedelta

log_getters_logger = get_logger('log_getters')


def fetch_logs_restapi(session, url, headers) -> tuple:
    try:
        response = session.get(url, headers=headers)
        status_code: int = response.status_code
        if status_code == 200:
            response_json = response.json()
            if response_json.get('value'):
                return response_json.get('value', []), response_json.get('nextLink', None)
            else:
                log_getters_logger.warning(f'Logger: The provided parameters resulted in an empty log set.')
                return None, None
        else:
            log_getters_logger.error(f'Error fetching logs from restapi. Status Code: {status_code}: {response.text}')
            return None, None
    except Exception as e:
        log_getters_logger.error(f'Exception occurred while fetching logs: {e}')
        return None, None


def get_azure_activity_restapi(sub_id: str, filter_start_time: str | None = None, filter_end_time: str | None = None, cor_id: str | None = None) -> list[dict]:
    auth_instance = AzureMonitorAuth()
    headers = auth_instance.chain_auth_restapi()
    if not headers:
        log_getters_logger.critical('Response from auth returned empty header.')
        return []

    if not filter_start_time or not filter_end_time:
        filter_end_time = datetime.utcnow()
        filter_start_time = filter_end_time - timedelta(days=1)

        filter_end_time = filter_end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        filter_start_time = filter_start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    if cor_id:
        url = (f"https://management.azure.com/subscriptions/{sub_id}/providers/microsoft.insights/eventtypes/management/values"
               f"?api-version=2015-04-01"
               f"&$filter=eventTimestamp ge '{filter_start_time}' and eventTimestamp le '{filter_end_time}' and correlationId eq '{cor_id}'")
    else:
        url = (f"https://management.azure.com/subscriptions/{sub_id}/providers/microsoft.insights/eventtypes/management/values"
               f"?api-version=2015-04-01"
               f"&$filter=eventTimestamp ge '{filter_start_time}' and eventTimestamp le '{filter_end_time}'")

    activity_logs = []

    session = requests.Session()
    while url:
        response_value, response_next = fetch_logs_restapi(session, url, headers)
        if response_value:
            activity_logs.extend(response_value)
        url = response_next
        log_getters_logger.info(f'[+] Collecting logs...')
    session.close()

    return activity_logs
