"""
Tool Name: Azure Activity Log Axe
Script Name: auth.py
Author: Nathan Eades
Date: 2024-06-01
Description: Control authentication to required Microsoft endpoint. Utilizes azure.identity.
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

from .logger import get_logger
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import AzureCliCredential
from azure.identity import AzurePowerShellCredential
from azure.identity import ChainedTokenCredential
# from azure.identity import ClientSecretCredential
from azure.identity import EnvironmentCredential
from azure.identity import InteractiveBrowserCredential

authentication_logger = get_logger("auth")


class AzureMonitorAuth:
    def __init__(self, tId: str | None = None, cId: str | None = None, cSecret: str | None = None):
        self.tId = tId
        self.cId = cId
        self.cSecret = cSecret

    def chain_auth_restapi(self) -> dict[str, str] | None:
        try:
            credential_chain = ChainedTokenCredential(
                EnvironmentCredential(),
                AzureCliCredential(),
                AzurePowerShellCredential(),
                InteractiveBrowserCredential()
            )
            access_token = credential_chain.get_token("https://management.azure.com/.default")
            token = access_token.token

            # return header + token
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept-Encoding': 'gzip, deflate'
            }
        except ClientAuthenticationError as e:
            authentication_logger.error(f"ClientAuthenticationError: {e}")
        except Exception as e:
            authentication_logger.error(f"General exception: {e}")
