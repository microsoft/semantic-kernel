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
- An updated [`appsettings.json`](../webapi/appsettings.json) file. At a minimum, you must fill out the `Completion` and `Embedding` sections per the instructions in the comments.

For more information on how to prepare this data, [see the full instructions for Copilot Chat](../README.md).

## 1. Configure your environment
### Windows
1. If you have not already, install PowerShell 6 or newer from https://learn.microsoft.com/powershell/scripting/install/installing-powershell.
   > You can run `$PSVersionTable.PSVersion` in PowerShell to verify the version.
1. Open a PowerShell window as an administrator, navigate to this directory, and run the following command:
   ```powershell
   ./Install-Requirements.ps1
   ```
   > This script uses the Chocolatey package manager install .NET 6.0 SDK, latest Node.js, and Yarn package manager.
   
### Linux
For all other operating systems, ensure NET 6.0 SDK (or newer), latest Node.js, and Yarn package manager are installed before proceeding.
> Be sure to install the classic (v1.22.19) Yarn package manager from https://classic.yarnpkg.com/.

## 2. Configure CopilotChat
Configure the projects with your AI service and application registration information from above.

**Powershell**
```powershell
./Configure.ps1 -AzureOpenAI -Endpoint {AZURE_OPENAI_ENDPOINT} -ApiKey {AZURE_OPENAI_API_KEY} -ClientId {CLIENT_ID}
```
> For OpenAI, replace `-AzureOpenAI` with `-OpenAI` and omit `-Endpoint`.

**Bash**
```bash
./Configure.sh --azureopenai --endpoint {AZURE_OPENAI_ENDPOINT} --apikey {AZURE_OPENAI_API_KEY} --clientid {CLIENT_ID}
```
> For OpenAI, replace `--azureopenai` with `--openai` and omit `--endpoint`.

> **Note:** The `Configure.ps1` and `Configure.sh` scripts have additional parameters for setting options such as AI models and Azure Active Directory tenant IDs.

## 3. Run Copilot Chat
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

# Troubleshooting
## 1. "A fatal error occurred. The folder [/usr/share/dotnet/host/fxr] does not exist" when running dotnet commands on Linux.
> From https://stackoverflow.com/questions/73753672/a-fatal-error-occurred-the-folder-usr-share-dotnet-host-fxr-does-not-exist

When .NET (Core) was first released for Linux, it was not yet available in the official Ubuntu repo. So instead, many of us added the Microsoft APT repo in order to install it. Now, the packages are part of the Ubuntu repo, and they are conflicting with the Microsoft packages. This error is a result of mixed packages.
```bash
# Remove all existing packages to get to a clean state:
sudo apt remove --assume-yes dotnet*;
sudo apt remove --assume-yes aspnetcore*;
sudo apt remove --assume-yes netstandard*;
# Set the Microsoft package provider priority
echo -e "Package: *\nPin: origin \"packages.microsoft.com\"\nPin-Priority: 1001" | sudo tee /etc/apt/preferences.d/99microsoft-dotnet.pref;
# Update and install dotnet
sudo apt update;
sudo apt install --assume-yes dotnet-sdk-6.0;
```