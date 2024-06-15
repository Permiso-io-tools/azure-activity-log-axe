<div align="center">
    <img width="50%" src="https://github.com/EadesCloudDef/azure-activity-log-axe/blob/main/images/Log-Axe.png">
</div>

# Azure Activity Log Axe
**Permiso:** [https://permiso.io](https://permiso.io)

**Release Date:** June 17th, 2024  
**Event:** fwd:cloudsec (Washington D.C.)

Azure Activity Log Axe is a continually developing tool that simplifies the transactional log format provided by Microsoft. The tool leverages the "Axe Key," a method created by Nathan Eades of the Permiso P0 Labs team. The Axe Key provides a more consistent grouping of the transactional events of an operation than the traditional built-in Correlation and Operation IDs.

The OperationId can fail to maintain consistency whenever additional statuses, such as "Accepted," exist among the events of an operation. In these cases, Microsoft changes the OperationId of the final status or when multiple "Accepted" statuses exist (there could be tens). This disrupts the flow of following a single operation from start to end. The Axe Key addresses this issue, ensuring a stronger grouping mechanism and corrects this flaw.

Permiso directly uses this method, derived from the need to fully understand an operation through a single grouped (Axe Keyed) operation (collapsed transaction). With this approach, you can:

- Understand an operation from start to end.
- Know key details such as the final status (success/failure), and subStatus (contains whether arbitrary operations were creations or updates).
- View any metadata such as requestbody and responsebody, which may exist across different events of the transactional operation events.

This comprehensive view enables better and quicker detection decisions by providing all the expected fields in one place.

Current testing indicates an average error rate of approximately 0.2%. This rate may vary and may be taken into consideration during use. Overall this grouping for our own detection use as been invaluable in providing greater consistency and reliability then built in correlation and operation Ids on their own. 

<div align="center">
    <img width="100%" src="https://github.com/EadesCloudDef/azure-activity-log-axe/blob/main/images/whatItDoes.png">
</div>

<br/>

*The following was an initial blog to help the security community understand how to use Azure Monitor Activity logs:*  
https://permiso.io/blog/azure-logs-breaking-through-the-cloud-cover

[-Nathan Eades: GitHub](https://github.com/EadesCloudDef)  
[-Nathan Eades: LinkedIn](https://www.linkedin.com/in/eadesclouddef/)
  
<br/>

## Using Azure Activity Log Axe

### Installation & Use
Installation:
> Run the following (a virtual env can be used if you choose): python3 -m pip install -r requirements.txt

To run the tool, you can run python against the directory itself or the \_\_main\_\_.py file:
>python3 /path/to/directory/azure-activity-log-axe --subscription-id \<id\>

<br/>

### Authentication

To authenticate, choose the method you would like to authenticate with. 

>For any method below, the identity requires the following Azure permission to the subscription(s) being called:  
>*Microsoft.Insights/eventtypes/values/Read*

The tool will currently support and try in sequence when ran, the following authentication mechanisms through the Azure Identity client library's ChainedTokenCredential:
- **EnvironmentCredential**: For a list of supported environment variables see [azure-identity environmentcredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.environmentcredential?view=azure-python)
    - *AZURE_AUTHORITY_HOST* is not necessary
- **AzureCliCredential**: Install and authenticate via the Azure CLI using "az login". Then run this tool the way you normally would.
- **AzurePowerShellCredential**: Install and authenticate via PowerShell using "Connect-AzAccount". Then run this tool the way you normally would.
- **InteractiveBrowserCredential**: Authenticate via browser, this will run automatically if the other options do not exist.

<br/>

### Commands & Options
#### Starting the Tool:
Whether normal use or the interactive mode command, the initial options to start the tool and retrieve data are:
> - Required: --subscription-id \<id\>
> - Optional: --start-time 2024-03-16T00:00:00.000000Z --end-time 2024-06-13T05:05:33.5555555Z  
>   If used, both start and end time must be provided. Defaults to the last 24 hours without providing start and end times.
> - Optional: --correlation-id \<corId\>  
>   If used, your start and end time must be within the time the correlationId exists or no data is returned (Microsoft's design)

<br/>

The interactive (Read-Eval-Print Loop) command will hold the data in memory while you manipulate it. All commands are available to interactive mode. 
Starting interactive mode:
> python3 azure-activity-log-axe --subscription-id \<id\> --start-time 2024-04-30T00:00:00.000000Z --end-time 2024-05-30T00:00:00.0000000Z **interactive**

<div align="center">
    <img width="100%" src="https://github.com/EadesCloudDef/azure-activity-log-axe/blob/main/images/Screenshot 2024-06-11 at 12.56.15 PM.png">
</div>

<br/>

#### Example Script Mode Executions:
<div align="center">
    <img width="75%" src="https://github.com/EadesCloudDef/azure-activity-log-axe/blob/main/images/normalHelp.png">
</div>

>python3 azure-activity-log-axe **--subscription-id** \<id\> **--start-time** 2024-05-10T00:00:00.000000Z **--end-time** 2024-06-10T05:05:33.5555555Z **--field-value-deselect** fieldName:value1,value2 **save-axe-keyed-data**
>
>python3 azure-activity-log-axe **--subscription-id** \<id\> **--start-time** 2024-05-10T00:00:00.000000Z **--end-time** 2024-06-10T05:05:33.5555555Z **--correlationId** \<id\> **--select** axeKey,caller,operationName,statusCounts **show-simplified-data**
>
>python3 azure-activity-log-axe **--subscription-id** \<id\> **--select** axeKey,caller,operationName,statusCounts **--output-type** csv **show-simplified-data**

<br/>

#### Example Interactive Mode Executions:
<div align="center">
    <img width="75%" src="https://github.com/EadesCloudDef/azure-activity-log-axe/blob/main/images/interactiveHelp.png">
</div>

> summary
>
> **show-simplified-data** **--select** axeKey,caller,operationName,resourceProviderName,startTime,endTime,ip **--field-value-deselect** fieldName1:value1 **--field-value-deselect** fieldName2:value1 **--field-value-select** fieldName:value1
>
> **show-simplified-data** **--field-value-select** fieldName:"This is a value",value2
>
> **save-axe-keyed-data** **--select** axeKey,caller,operationName,resourceProviderName,startTime,endTime,ip **--field-value-deselect** fieldName:value1 **--field-value-deselect** fieldName:value1 **--field-value-select** fieldName:value1 **--output-type** csv **--filepath** /Users/test/Desktop/testDir/test.csv

<br/>

#### Option Notes:
> - Interactive Mode: Saving to a custom path on Windows will require escaped paths: C:\\\\user\Documents\\\\Test\\\\TestOut.csv  **OR**  a quoted path "C:\\user\Documents\\Test\\TestOut.csv"
> - --field-value-select and --field-value-deselect can both be used more than once to affect different fields

<br/>

<br/>


If there are more requests for one item over the others, reprioritization may occur.  

### Roadmap
| Feature    | Priority | Timeline (Quarter Year)
| -------- | ------- | ------- |
| Pull from & Support Schema of Azure Storage  | HIGH    |  Q3 24      |
| AG Grid Browser Viewer - Interactive Mode Option  | HIGH    |  Q3 24      |
| Show Schema / Fields Helper Command  | HIGH    |  Q3 24      |
| Pull from & Support Schema of Azure Log Analytics Workspace | MEDIUM     |  Q4 24      |
| Read from & Verify Support of JSON Lines or dict[list] File  | MEDIUM    |  Q4 24 - Q1 25       |
| Additional Built-In Summarizations  | MEDIUM    |  Q4 24 - Q1 25       |
| Secondary Axe Keying to Further Lower Error Rate  | MEDIUM    |  Q1 25 - Q2 25       |
| Option to Pull from All Subscriptions Available  | LOW    |  Q1 25 - Q2 25       |
| Splunk TA w/ Custom Command Functions for Axe Keyed & Simplified Data  | LOW    |  Q1 25 - Q2 25       |

<br/>

## Microsoft Sentinel Axe Key Query
```cs
AzureActivity
| extend correlationId = tolower(CorrelationId)
| extend operationName = tolower(OperationNameValue)
| extend resourceId = tolower(_ResourceId)
| extend axeKey = hash_md5(strcat(correlationId,":",operationName,":",resourceId))
| extend status = tolower(ActivityStatusValue)
| extend subStatus = tolower(ActivitySubstatusValue)
| extend requestBody = tolower(Properties_d.requestbody)
| extend responseBody = tolower(Properties_d.responseBody)
| extend category = tolower(CategoryValue)
| summarize take_any(correlationId),
            take_any(category),
            take_any(operationName),
            startTime = min(TimeGenerated), 
            endTime = max(TimeGenerated),
            normalSubStatus = make_set_if(subStatus, isnotempty(subStatus) and status != "failure"),
            failedSubStatus = make_set_if(subStatus, isnotempty(subStatus) and status == "failure"),
            statuses = make_set(status),
            finalStatus = arg_max(TimeGenerated,status)[1],
            statusCounts = bag_pack("started", countif(status in ("start","started")), "accepted", countif(status in ("accept","accepted")), "failed", countif(status in ("failure","failed")), "succeeded", countif(status in ("success","succeeded"))),
            take_any(requestBody),
            take_any(responseBody),
            make_set(Claims_d),
            take_any(resourceId)
        by axeKey
```
