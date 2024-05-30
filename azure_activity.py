import azure_logger
import json
import requests
import simplify_key
from auth import AzureMonitorAuth

azure_activity_logger = azure_logger.get_logger("azure_activity")


def get_azure_activity_restapi(subId: str | None) -> list[dict] :
    auth_instance = AzureMonitorAuth()
    headers = auth_instance.chain_auth_restapi()
    if not headers:
        azure_activity_logger.critical(f"Response from auth returned empty header.")
        return

    # if not subId:
    #     sub_url: str = "https://management.azure.com/subscriptions?api-version=2022-12-01"
    #     sub_response: requests.Response = requests.get(sub_url, headers=headers)
    #     subscriptions: list = response.json().get('value', [])

    # if len(subscriptions) > 0:
    #     for subscription in subscriptions:
    #         url = (f"https://management.azure.com/subscriptions/{subscription_id}/providers/microsoft.insights/eventtypes/management/values"
    #                 f"?api-version=2015-04-01"
    #                 f"&$filter=eventTimestamp ge '2024-05-01T20:00:00Z' and eventTimestamp le '2024-05-12T20:00:00Z' and correlationId eq '1f63a42a-017a-4e86-9a16-53645cbf36c5'")

    url = (f"https://management.azure.com/subscriptions/{subId}/providers/microsoft.insights/eventtypes/management/values"
        f"?api-version=2015-04-01"
        f"&$filter=eventTimestamp ge '2024-05-01T20:00:00Z' and eventTimestamp le '2024-05-12T20:00:00Z'")

    response = requests.get(url, headers=headers)
    response_json: dict = response.json()
    response_value: list[dict] | None = response_json.get("value", None)
    response_next: str | None = response_json.get("nextLink", None)

    activity_logs: list = []
    if response_value:
        activity_logs.extend(response_value)
    while response_next:
        response = requests.get(response_next, headers=headers)
        response_json: dict = response.json()
        response_value: list[dict] | None = response_json.get("value", None)
        response_next: str | None = response_json.get("nextLink", None)
        if response_value:
            activity_logs.extend(response_value)

    return activity_logs

# def read_azure_monitor_file():
#     print("d")



def read_azure_monitor_stream(event_array: list[dict]):
    if event_array:
        for raw_event in event_array:
            operationName = raw_event.get("operationName").get("value")
            print(operationName)
    else:
        print("fail")
        #logger error