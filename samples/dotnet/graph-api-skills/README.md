# Graph API Skill Example

This example program demonstrates how to use the Microsoft Graph API skills with the Semantic Kernel.

## Setup

1. Create an `appsettings.Development.json` file next to `appsettings.json`.
   - The `appsettings.Development.json` file should be ignored by git and will not be checked in by default.
2. Set your API Keys
   - This example can use either Azure OpenAI or OpenAI models for summarization.
   - In your `appsettings.Development.json` fill out the `OpenAI` and/or `AzureOpenAI` sections with an appropriate label and API key.
3. If you have not already, [register an application with the Microsoft identity platform](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app).
   - Select **`Mobile and desktop applications`** as platform type, and the Redirect URI will be **`http://localhost`**
   - It is recommended you use the **`Personal Microsoft accounts`** account type for this sample.
   - Make sure the API permissions include the scopes outines in your `appsettings.json` (e.g. Mail.Send, ...).
4. Update the `MsGraph` sections in your `appsettings.json` with your application registrations IDs and parameters.
5. Update the `OneDrivePathToFile` to point to a text file that exists in your OneDrive.
   - This file will be used as content to summarize in the example.

Example `appsettings.Development.json`:

```json
{
  "MsGraph": {
    "ClientId": "YOUR_APPLICATION_CLIENTID",
    "RedirectUri": "http://localhost"
  },
  "OneDrivePathToFile": "Documents/MyFile.txt",
  "OpenAI": {
    "Label": "text-davinci-003",
    "ApiKey": "YOUR_OPENAPI_KEY"
  },
  "AzureOpenAI": {
    "Label": "azure-text-davinci-003",
    "DeploymentName": "azure-text-davinci-003",
    "Endpoint": "YOUR_AZURE_OPENAI_ENDPOINT (e.g. https://contoso.openai.azure.com/",
    "ApiKey": "YOUR_AZURE_OPENAPI_KEY"
  }
}
```
