# Booking Restaurant - Demo Application

This sample provides a practical demonstration of how to leverage features from the [Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel) to build a console application. Specifically, the application utilizes the [Business Schedule and Booking API](https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app) through Microsoft Graph to enable a Large Language Model (LLM) to book restaurant appointments efficiently. This guide will walk you through the necessary steps to integrate these technologies seamlessly.

## Semantic Kernel Features Used

- [Plugin](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/Functions/KernelPlugin.cs) - Creating a Plugin from a native C# Booking class to be used by the Kernel to interact with Bookings API.
- [Chat Completion Service](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service [OpenAI Connector implementation](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/ChatCompletion/OpenAIChatCompletionService.cs) to generate responses from the LLM.
- [Chat History](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/ChatHistory.cs) Using the Chat History abstraction to create, update and retrieve chat history from Chat Completion Models.
- [Auto Function Calling](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/AutoFunctionCalling/OpenAI_FunctionCalling.cs) Enables the LLM to have knowledge of current importedUsing the Function Calling feature automatically call the Booking Plugin from the LLM.

## Prerequisites

- [.NET 8](https://dotnet.microsoft.com/download/dotnet/8.0).
- [Microsoft 365 Business License](https://www.microsoft.com/en-us/microsoft-365/business/compare-all-microsoft-365-business-products) to use [Business Schedule and Booking API](https://www.microsoft.com/en-us/microsoft-365/business/scheduling-and-booking-app).
- [Azure Entra Id](https://www.microsoft.com/en-us/security/business/identity-access/microsoft-entra-id) administrator account to register an application and set the necessary credentials and permissions.

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

ℹ️ OpenAI Models older than 0613 version do not support function calling.

ℹ️ When using Azure OpenAI, ensure that the model name of your deployment matches any of the above supported models names.

## Configuring the sample

The sample can be configured by using the command line with .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests.

### Create an App Registration in Azure Active Directory

1. Go to the [Azure Portal](https://portal.azure.com/).
2. Select the Azure Active Directory service.
3. Select App registrations and click on New registration.
4. Fill in the required fields and click on Register.
5. Copy the Application **(client) Id** for later use.
6. Save Directory **(tenant) Id** for later use..
7. Click on Certificates & secrets and create a new client secret. (Any name and expiration date will work)
8. Copy the **client secret** value for later use.
9. Click on API permissions and add the following permissions:
   - Microsoft Graph
     - Application permissions
       - BookingsAppointment.ReadWrite.All
     - Delegated permissions
       - OpenId permissions
         - offline_access
         - profile
         - openid

### Create Or Use a Booking Service and Business

1. Go to the [Bookings Homepage](https://outlook.office.com/bookings) website.
2. Create a new Booking Page and add a Service to the Booking (Skip if you don't ).
3. Access [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer)
4. Run the following query to get the Booking Business Id:
   ```http
   GET https://graph.microsoft.com/v1.0/solutions/bookingBusinesses
   ```
5. Copy the **Booking Business Id** for later use.
6. Run the following query and replace it with your **Booking Business Id** to get the Booking Service Id
   ```http
   GET https://graph.microsoft.com/v1.0/solutions/bookingBusinesses/{bookingBusiness-id}/services
   ```
7. Copy the **Booking Service Id** for later use.

### Using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)

```powershell
dotnet user-secrets set "BookingServiceId" " .. your Booking Service Id .. "
dotnet user-secrets set "BookingBusinessId" " .. your Booking Business Id ..  "

dotnet user-secrets set "AzureEntraId:TenantId" " ... your tenant id ... "
dotnet user-secrets set "AzureEntraId:ClientId" " ... your client id ... "

# App Registration Authentication
dotnet user-secrets set "AzureEntraId:ClientSecret" " ... your client secret ... "
# OR User Authentication (Interactive)
dotnet user-secrets set "AzureEntraId:InteractiveBrowserAuthentication" "true"
dotnet user-secrets set "AzureEntraId:RedirectUri" " ... your redirect uri ... "

# OpenAI (Not required if using Azure OpenAI)
dotnet user-secrets set "OpenAI:ModelId" "gpt-3.5-turbo"
dotnet user-secrets set "OpenAI:ApiKey" "... your api key ... "
dotnet user-secrets set "OpenAI:OrgId" "... your ord ID ... " # (Optional)

# Using Azure OpenAI (Not required if using OpenAI)
dotnet user-secrets set "AzureOpenAI:DeploymentName" " ... your deployment name ... "
dotnet user-secrets set "AzureOpenAI:ApiKey" " ... your api key ... "
dotnet user-secrets set "AzureOpenAI:Endpoint" " ... your endpoint ... "
```

## Running the sample

After configuring the sample, to build and run the console application just hit `F5`.

To build and run the console application from the terminal use the following commands:

```powershell
dotnet build
dotnet run
```

### Example of a conversation

> **User** > Please book a restaurant for me.

> **Assistant** > Sure, I can help you with that. Could you please provide me with the following information:
>
> 1.  Name of the restaurant you would like to book.
> 2.  Date and time of the reservation.
> 3.  Number of people in your party.
> 4.  Your name.
> 5.  Your email address.
> 6.  Your phone number.
>
> Once I have all this information, I will proceed with the booking.

> **User** > I would like to book a table at the restaurant "The French Laundry" on the 15th of March at 7:00 PM for 4 people. My name is John Doe, my email address is john@internet.com, and my phone number is 123-456-7890.

> **System** > Do you want to book a table at The French Laundry on 15/03/2023 19:00:00 for 4 people?

> **System** > Please confirm by typing 'yes' or 'no'.

> **User** > yes

> **Assistant** > Great! I have successfully booked a table for you at "The French Laundry" on the 15th of March at 7:00 PM for 4 people.
>
> Your reservation has been made under the name John Doe.
>
> If you have any further questions or need to make any changes to your reservation, please let me know.

> **User** > List my current bookings

> **Assistant** > You currently have one booking:
>
> - Restaurant: The French Laundry
> - Date and Time: 15th of March at 7:00 PM
> - Party Size: 4 people
>
> If you need any further assistance or if there's anything else I can help you with, please let me know.

> **User** > Cancel my booking

> **System** > `[Cancelling a reservation for 4 at The French Laundry on 2023-03-15 at 19:00:00]`

> **Assistant** > I have successfully canceled your booking at "The French Laundry" on the 15th of March at 7:00 PM for 4 people.
>
> If you have any other questions or need further assistance, please let me know.
