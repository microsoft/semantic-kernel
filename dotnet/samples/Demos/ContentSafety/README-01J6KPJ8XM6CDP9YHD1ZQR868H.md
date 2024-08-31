---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:56:37Z
---

# Azure AI Content Safety and Prompt Shields service example

This sample provides a practical demonstration of how to leverage [Semantic Kernel Prompt Filters](ht*******************************************************************************************er) feature together with prompt verification services such as Azure AI Content Safety and Prompt Shields.

[Azure AI Content Safety](ht***********************************************************************ew) detects harmful user-generated and AI-generated content in applications and services. Azure AI Content Safety includes text and image APIs that allow to detect material that is harmful.

[Prompt Shields](ht***********************************************************************************ak) service allows to check your large language model (LLM) inputs for both User Prompt and Document attacks.

Together with Semantic Kernel Prompt Filters, it's possible to define detection logic in dedicated place and avoid mixing it with business logic in applications.

## Prerequisites

1. [OpenAI](ht*****************************************on) subscription.
2. [Azure](ht****************************ee) subscription.
3. Once you have your Azure subscription, create a [Content Safety resource](ht*********************te) in the Azure portal to get your key and endpoint. Enter a unique name for your resource, select your subscription, and select a resource group, supported region (East US or West Europe), and supported pricing tier. Then select **Create**.
4. Update `appsettings.json/appsettings.Development.json` file with your configuration for `OpenAI` and `AzureContentSafety` sections or use .NET [Secret Manager](ht**************************************************************ts):

```powershell {"id":"01J6KPZ7Y1YC06AFDVQDQB85Z1"}
# Azure AI Content Safety
dotnet user-secrets set "AzureContentSafety:Endpoint" "... your endpoint ..."
dotnet user-secrets set "AzureContentSafety:ApiKey" "... your api key ... "

# OpenAI
dotnet user-secrets set "OpenAI:ChatModelId" "... your model ..."
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ... "
```

## Testing

1. Start ASP.NET Web API application.
2. Open `ContentSafety.http` file. This file contains HTTP requests for following scenarios:
   - No offensive/attack content in request body - the response should be `200 OK`.
   - Offensive content in request body, which won't pass text moderation analysis - the response should be `400 Bad Request`.
   - Attack content in request body, which won't pass Prompt Shield analysis - the response should be `400 Bad Request`.

It's possible to send [HTTP re****ts](ht*****************************************************************************.0) directly from `ContentSafety.http` with Visual Studio 2022 version 17.8 or later. For Visual Studio Code users, use `ContentSafety.http` file as REST API specification and use tool of your choice to send described requests.

## More information

- [What is Azure AI Content Safety?](ht***********************************************************************ew)
- [Analyze text content with Azure AI Content Safety](ht******************************************************************************xt)
- [Detect attacks with Azure AI Content Safety Prompt Shields](ht***********************************************************************************ak)
