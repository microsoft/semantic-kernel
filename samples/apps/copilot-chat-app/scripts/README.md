# Copilot Chat Setup Scripts

> The PowerShell scripts in this directory require [PowerShell Core 6 or higher](https://github.com/PowerShell/PowerShell#get-powershell).

## Before You Begin
To run Copilot Chat, you will need the following:
- *Application ID*
  - This is the Client ID (i.e., Application ID) associated with your Azure Active Directory (AAD) application registration, which you can find in the Azure portal.
- *Tenant ID*
  - This is the Tenant ID (i.e., Directory ID) associated with your AAD app registration.
  [Learn more about possible values for this parameter](https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-client-application-configuration#authority).
- *Azure OpenAI or OpenAI API Key*
  - This is your API key for Azure OpenAI or OpenAI

You also need to update [`appsettings.json`](../webapi/appsettings.json) with the relevant deployment or model information, as well as endpoint if you are using Azure OpenAI.

For more information on how to prepare this data, [see the full instructions for Copilot Chat](../README.md).

## 1. Configure your environment
### Windows
1. Open a PowerShell window as an administrator, navigate to this directory, and run the following command:
   ```powershell
   ./Install-Requirements.ps1
   ```
   > This script uses the Chocolatey package manager install .NET 6.0 SDK, latest Node.js, and Yarn package manager.
   For all other operating systems, ensure these requirements are installed before proceeding.

   > Be sure to install the classic (v1.22.19) Yarn package manager from https://classic.yarnpkg.com/.

1. Configure the projects with your AI service and application registration information from above.
   > The `Configure.ps1` script has additional parameters for setting options such as AI models and Azure Active Directory tenant IDs.
   
   For Azure OpenAI:
   ```powershell
   ./Configure.ps1 -AzureOpenAI -Endpoint {AZURE_OPENAI_ENDPOINT} -ApiKey {AZURE_OPENAI_API_KEY} -ClientId {CLIENT_ID}
   ```
   For OpenAI:
   ```powershell
   ./Configure.ps1 -OpenAI -ApiKey {OPENAI_API_KEY} -ClientId {CLIENT_ID}
   ```

## 2. Run Copilot Chat
The `Start` script initializes and runs the WebApp (frontend) and WebApi (backend) for Copilot Chat on your local machine.

### PowerShell
Open a PowerShell window, navigate to this directory, and run the following command:
> Use the `Application ID` and `Tenant ID` from above.
```powershell
./Start.ps1
```

### Bash
Open a Bash window and navigate to this directory. First, ensure the `Start.sh` script is executable:
```bash
chmod +x Start.sh
```

Then run the following command:
```bash
./Start.sh
```
Note that this script starts `CopilotChatWebApi.exe` as a background process. Be sure to terminate it when you are finished.
