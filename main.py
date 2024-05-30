from azure_activity import get_azure_activity_restapi, read_azure_monitor_stream

# def get_azure_simplify_key()

# url = (f"https://management.azure.com/subscriptions/{subscription_id}/"
#        f"resourceGroups/{resource_group}/providers/{provider}/"
#        f"{resource_type}/{resource_name}/providers/microsoft.insights/logs?"
#        f"api-version={api_version}")

# Make the API call
# response = requests.get(url, headers=headers)
# data = response.json()

# print(read_azure_monitor_stream(data))
# Process and print the data
# with open ("/Users/neades/Desktop/azureKey/out.json", "w") as out:
#     out.write(json.dumps(data, indent=4))

def main():
    logDict = get_azure_activity_restapi("")
    print(read_azure_monitor_stream(logDict))

if __name__ == '__main__':
    main()