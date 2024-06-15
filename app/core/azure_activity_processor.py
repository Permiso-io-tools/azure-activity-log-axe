"""
Tool Name: Azure Activity Log Axe
Script Name: azure_activity_processor.py
Author: Nathan Eades
Date: 2024-06-01
Description: Log data processor, retrieves and applies axe key, consolidates data for simplified structure and use.
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

import json
from .azure_axe_key import get_axe_key
from datetime import datetime
from typing import Optional, Any
from app.utils.logger import get_logger

azure_activity_logger = get_logger('azure_activity')


class AzureActivityProcessor:
    def __init__(self):
        # Basic azure activity data with simplify key
        self.keyed_log_data: list[dict] = []
        self.summary_keyed_log_data: dict = {}

        # Simplified azure activity data
        # self.simplified_log_data_objects = {} #replaced with get_simplified_azure_activity return to limit memory use
        self.simplified_log_data_list: list[dict] = []

    # Build and apply axeKey to original logs
    def get_axe_key_azure_activity(self, activity_logs: list[dict]) -> None:
        if not activity_logs:
            azure_activity_logger.critical(f'No activity logs exist to add the simplify key.')
            return

        for raw_event in activity_logs:
            cor_id = raw_event.get('correlationId')
            operation_name = raw_event.get('operationName').get('value')
            resource_id = raw_event.get('resourceId')
            axe_key = get_axe_key(cor_id, operation_name, resource_id)
            if axe_key:
                raw_event['axeKey'] = axe_key
                self.keyed_log_data.append(raw_event)
            else:
                azure_activity_logger.warning(f'Failed to add simplify key to raw_event: {raw_event}')

        self.summary_keyed_log_data = {}

    # Build new list of objects simplifying data and grouping transactional operations
    def get_simplified_azure_activity(self, keyed_log_data: list[dict]) -> None:
        simplified_log_data_objects = {}
        if not keyed_log_data:
            azure_activity_logger.critical(f'No keyed log data exists.')
            return

        for raw_event in keyed_log_data:
            axe_key = raw_event.get('axeKey')
            if axe_key:
                if axe_key not in simplified_log_data_objects:
                    # Initialize the dict for the axe_key with serializable values
                    simplified_log_data_objects[axe_key] = {
                        'caller': None,
                        'operationName': None,
                        'operationNameLocalized': None,
                        'startTime': None,
                        'endTime': None,
                        'ip': None,
                        'subStatuses': [],
                        'subStatusCounts': {},
                        'startStatus': None,
                        'endStatus': None,
                        'statuses': [],
                        'statusCounts': {},
                        'subscriptionId': None,
                        'claims': {},
                        'requestBody': {},
                        'responseBody': {},
                        'category': None,
                        'level': None,
                        'resourceGroupName': None,
                        'resourceId': None,
                        'eventDataIds': [],
                        'correlationId': None,
                        'operationIds': set()
                    }

                ### --- Collect fields per simplify key --- ###
                simplified_event = simplified_log_data_objects[axe_key]
                simplified_event['caller'] = self.get_object_value(raw_event, 'caller')
                simplified_event['operationName'] = self.get_object_value(raw_event, 'operationName', 'value').lower()
                simplified_event['operationNameLocalized'] = self.get_object_value(raw_event, 'operationName', 'localizedValue')
                simplified_event['ip'] = self.get_object_value(raw_event, 'httpRequest', 'clientIpAddress') or self.get_object_value(raw_event, 'claims', 'ipaddr')
                simplified_event['subscriptionId'] = self.get_object_value(raw_event, 'subscriptionId')
                simplified_event['category'] = self.get_object_value(raw_event, 'category', 'value')
                simplified_event['level'] = self.get_object_value(raw_event, 'level')
                simplified_event['resourceProviderName'] = self.get_object_value(raw_event, 'resourceProviderName', 'value').lower()
                simplified_event['resourceGroupName'] = self.get_object_value(raw_event, 'resourceGroupName')
                simplified_event['resourceId'] = self.get_object_value(raw_event, 'resourceId')
                simplified_event['correlationId'] = self.get_object_value(raw_event, 'correlationId')

                # subStatus & status
                sub_status: str = self.get_object_value(raw_event, 'subStatus', 'value')
                if sub_status:
                    substatus_element: Optional[int] = self.get_object_value(simplified_event['subStatusCounts'], sub_status)
                    if substatus_element is None:
                        simplified_event['subStatusCounts'][sub_status] = 1
                    else:
                        simplified_event['subStatusCounts'][sub_status] += 1

                    if sub_status not in simplified_event['subStatuses']:
                        simplified_event['subStatuses'].append(sub_status)
                status: str = self.get_object_value(raw_event, 'status', 'value')
                if status:
                    status_element: Optional[int] = self.get_object_value(simplified_event['statusCounts'], status)
                    if status_element is None:
                        simplified_event['statusCounts'][status] = 1
                    else:
                        simplified_event['statusCounts'][status] += 1

                    if status not in simplified_event['statuses']:
                        simplified_event['statuses'].append(status)

                # Start & End (Time / Status)
                date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
                event_time = self.get_object_value(raw_event, 'eventTimestamp')
                if event_time:
                    if '.' in event_time:
                        if len(event_time.split('.')[-1]) > 6:
                            # Trim the fractional seconds to 6 digits (Python iso rec)
                            event_time = event_time[:-1][:26] + 'Z'
                    else:
                        event_time = event_time[:-1] + '.000000Z'
                    try:
                        event_time = datetime.strptime(event_time, date_format)
                    except ValueError as e:
                        azure_activity_logger.error(f"Error parsing event time {event_time}: {e}")
                        continue
                if not simplified_event['startTime'] or event_time < datetime.strptime(simplified_event['startTime'], date_format):
                    simplified_event['startTime'] = event_time.strftime(date_format)
                    simplified_event['startStatus'] = raw_event['status']['value']

                if not simplified_event['endTime'] or event_time > datetime.strptime(simplified_event['endTime'], date_format):
                    simplified_event['endTime'] = event_time.strftime(date_format)
                    simplified_event['endStatus'] = raw_event['status']['value']

                # claims
                claim_appid: str = self.get_object_value(raw_event, 'claims', 'appid')
                if claim_appid:
                    simplified_event['claims']['appid'] = claim_appid
                claim_appidacr: str = self.get_object_value(raw_event, 'claims', 'appidacr')
                if claim_appidacr:
                    simplified_event['claims']['appidacr'] = claim_appidacr
                claim_idtyp: str = self.get_object_value(raw_event, 'claims', 'idtyp')
                if claim_idtyp:
                    simplified_event['claims']['idtyp'] = claim_idtyp
                claim_uti: str = self.get_object_value(raw_event, 'claims', 'uti')
                if claim_uti:
                    simplified_event['claims']['uti'] = claim_uti
                claim_authnmethodsreferences: str = self.get_object_value(raw_event, 'claims', 'http://schemas.microsoft.com/claims/authnmethodsreferences')
                if claim_authnmethodsreferences:
                    simplified_event['claims']['authnmethodsreferences'] = claim_authnmethodsreferences

                # body fields
                request_body: str = self.get_object_value(raw_event, 'properties', 'requestbody')
                if request_body:
                    simplified_event['requestBody'] = json.loads(request_body)
                response_body: str = self.get_object_value(raw_event, 'properties', 'responseBody')
                if response_body:
                    simplified_event['responseBody'] = json.loads(response_body)

                # event Ids
                id: str = self.get_object_value(raw_event, 'eventDataId')
                if id:
                    simplified_event['eventDataIds'].append(id)

                # operation Ids
                id: str = self.get_object_value(raw_event, 'operationId')
                if id:
                    simplified_event['operationIds'].add(id)
        for simplified_event in simplified_log_data_objects.values():
            simplified_event['operationIds'] = list(simplified_event['operationIds'])
        return simplified_log_data_objects

    # Re-orient data to simplify structure. Ensures axeKey is part of the log dict, not a parent element.
    def get_simplified_azure_activity_list(self, simplified_azure_activity_object: dict) -> None:
        for key, value in simplified_azure_activity_object.items():
            full_event = {'axeKey': key}
            full_event.update(value)

            self.simplified_log_data_list.append(full_event)

    def get_object_value(self, dictObject: dict, *keys) -> Optional[Any]:
        value: Any = dictObject
        for key in keys:
            value = value.get(key)
            if value is None:
                # azure_activity_logger.warning(f'The provided key did not return a value: {key}.')
                return None
        return value

    def get_unique_values(self, dictObjectList: list[dict], *keys) -> list:
        if not dictObjectList:
            azure_activity_logger.warning('No activity logs exist.')
            return []

        unique_values = set()
        for raw_event in dictObjectList:
            value: Any = self.get_object_value(raw_event, *keys)
            if value is not None and not isinstance(value, dict):
                unique_values.add(value)
            else:
                azure_activity_logger.warning(f'The result from the key was a dict: {keys}, value: {value}.')

        if not unique_values:
            azure_activity_logger.warning(f'No unique values found for key: {keys}.')
            return []

        return sorted(unique_values)

    def get_unique_values_count(self, unique_values: list) -> int:
        if not unique_values:
            azure_activity_logger.warning('No unique values.')
            return 0

        return len(unique_values)

    def get_keyed_event_count(self) -> int:
        if self.keyed_log_data:
            return len(self.keyed_log_data)
        azure_activity_logger.warning(f'Keyed log is empty.')
        return 0

    # Note to self: May move this to allow filters
    def get_keyed_log_summary(self) -> dict:
        self.summary_keyed_log_data['Total Event Count'] = self.get_keyed_event_count()
        self.summary_keyed_log_data['Axe Key Count'] = self.get_unique_values_count(self.get_unique_values(self.keyed_log_data, 'axeKey'))
        self.summary_keyed_log_data['Correlation Id Count'] = self.get_unique_values_count(self.get_unique_values(self.keyed_log_data, 'correlationId'))
        self.summary_keyed_log_data['Operation Id Count'] = self.get_unique_values_count(self.get_unique_values(self.keyed_log_data, 'operationId'))
        self.summary_keyed_log_data['Operation Name Count'] = self.get_unique_values_count(self.get_unique_values(self.keyed_log_data, 'operationName', 'value'))
        self.summary_keyed_log_data['Resource Provider Name Count'] = self.get_unique_values_count(self.get_unique_values(self.keyed_log_data, 'resourceProviderName', 'value'))
