from azure.core.exceptions import ClientAuthenticationError
from azure.identity import (
    ChainedTokenCredential,
    EnvironmentCredential,
    AzureCliCredential,
    AzurePowerShellCredential,
    InteractiveBrowserCredential,
    ClientSecretCredential
)
import azure_logger

authentication_logger = azure_logger.get_logger("authenticate")

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
            token = credential_chain.get_token("https://management.azure.com/.default").token

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

    def sp_client_secret_auth_restapi(self) -> dict[str, str] | None:
        try:
            if self.tId and self.cId and self.cSecret:
                credential = ClientSecretCredential(self.tId, self.cId, self.cSecret)
                token = credential.get_token("https://management.azure.com/.default").token

                # return header + token
                return {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'Accept-Encoding': 'gzip, deflate'
                }
            else:
                print("Tenant ID, Client ID, and Client Secret must be provided for Service Principal authentication.")
        except ClientAuthenticationError as e:
            authentication_logger.error(f"ClientAuthenticationError: {e}")
        except Exception as e:
            authentication_logger.error(f"General exception: {e}")