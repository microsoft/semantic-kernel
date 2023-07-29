# Copilot Chat Setup Scripts (local deployment)

## Before You Begin
To run Copilot Chat, you will need the following:
- *Application ID*
  - This is the Client ID (i.e., Application ID) associated with your Azure Active Directory (AAD) application registration, which you can find in the Azure portal.
- *Azure OpenAI or OpenAI API Key*
  - This is your API key for Azure OpenAI or OpenAI

## 1. Configure your environment
### Windows
Open a PowerShell terminal as an administrator, navigate to this directory, and run the following command:
```powershell
./Install-Requirements.ps1
```
> This script uses the Chocolatey package manager install .NET 6.0 SDK, latest Node.js, and Yarn package manager.
   
### Ubuntu/Debian Linux
Open a bash terminal as an administrator, navigate to this directory, and run the following command:
```bash
./Install-Requirements-UbuntuDebian.ps1
```

### Other Linux/MacOS
For all other operating systems, ensure NET 6.0 SDK (or newer), Node.js 14 (or newer), and Yarn classic ([v1.22.19](https://classic.yarnpkg.com/)) package manager are installed before proceeding.

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

> **Note:** `Configure.ps1`/`Configure.sh` scripts also have parameters for setting additional options, such as AI models and Azure Active Directory tenant IDs.

## 3. Run Copilot Chat
The `Start` script initializes and runs the WebApp (frontend) and WebApi (backend) for Copilot Chat on your local machine.

### PowerShell
Open a PowerShell window, navigate to this directory, and run the following command:
```powershell
./Start.ps1
```

### Bash
Open a Bash window, navigate to this directory, and run the following commands:
```bash
# Ensure ./Start.sh is executable
chmod +x Start.sh
# Start CopilotChat 
./Start.sh
```
> **Note:** The first time you run this may take a few minutes for Yarn packages to install.
> **Note:** This script starts `CopilotChatWebApi.exe` as a background process. Be sure to terminate it when you are finished.

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
sudo apt install --assume-yes dotnet-sdk-7.0;
```
