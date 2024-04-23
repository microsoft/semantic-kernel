# Booking Restaurant - Demo Application

This sample provides a practical demonstration of how to leverage features from the [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel) to build a console application. Specifically, the application utilizes the [Business Schedule and Booking API](https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app) through Microsoft Graph to enable a Large Language Model (LLM) to book restaurant appointments efficiently. This guide will walk you through the necessary steps to integrate these technologies seamlessly.

## Semantic Kernel Features Used

- [Plugin] Using the Kernel Plugin concept to create a Booking Plugin which runs native code to interact with Bookings API.
- [Chat Completion Service] Using the Chat Completion Service available in OpenAI [Connector] to generate responses from the LLM.
- [Chat History] Using the Chat History abstraction to create, update and retrieve chat history from Chat Completion Models.
- [Prompt Execution Settings] Using the Prompt Execution Settings feature to specify a desired configuration when the executing prompts.
- [Auto Function Calling] Enables the LLM to have knowledge of current importedUsing the Function Calling feature automatically call the Booking Plugin from the LLM.

## Prerequisites

- [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0).
- [Microsoft 365 Business License](https://www.microsoft.com/en-us/microsoft-365/business/compare-all-microsoft-365-business-products) to use [Business Schedule and Booking API](https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app).

### Function Calling Enabled Models

This sample uses function calling capable models and has been tested with the following models:

| Model type      | Model name/id             |       Model version | Supported |
| --------------- | ------------------------- | ------------------: | --------- |
| Chat Completion | gpt-3.5-turbo             |                0125 | ✅        |
| Chat Completion | gpt-3.5-turbo-1106        |                1106 | ✅        |
| Chat Completion | gpt-3.5-turbo-0613        |                0613 | ✅        |
| Chat Completion | gpt-3.5-turbo-0301        |                0301 | ❌        |
| Chat Completion | gpt-3.5-turbo-16k         |                0613 | ✅        |
| Chat Completion | gpt-4                     |                0613 | ✅        |
| Chat Completion | gpt-4-0613                |                0613 | ✅        |
| Chat Completion | gpt-4-0314                |                0314 | ❌        |
| Chat Completion | gpt-4-turbo               |          2024-04-09 | ✅        |
| Chat Completion | gpt-4-turbo-2024-04-09    |          2024-04-09 | ✅        |
| Chat Completion | gpt-4-turbo-preview       |        0125-preview | ✅        |
| Chat Completion | gpt-4-0125-preview        |        0125-preview | ✅        |
| Chat Completion | gpt-4-vision-preview      | 1106-vision-preview | ✅        |
| Chat Completion | gpt-4-1106-vision-preview | 1106-vision-preview | ✅        |

OpenAI Models older than 0613 version do not support function calling.

When using Azure OpenAI, ensure that the model name of your deployment matches any of the above supported models names.

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

```powershell
dotnet user-secrets set "BookingServiceId" " .. your Booking Service Id .. "
dotnet user-secrets set "BookingBusinessId" " .. your Booking Business Id ..  "

# OpenAI (Not required if using Azure OpenAI)
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo"
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ..."
dotnet user-secrets set "OpenAI:OrgId" "... your ord ID ..." # (Optional)

# Using Azure OpenAI (Not required if using OpenAI)
dotnet user-secrets set "AzureOpenAI:DeploymentName" " ... your deployment name ..."
dotnet user-secrets set "AzureOpenAI:ApiKey" " ... your api key ..."
dotnet user-secrets set "AzureOpenAI:Endpoint" " ... your endpoint ..."
```

## Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```
