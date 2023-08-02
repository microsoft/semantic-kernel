# Deploying Copilot Chat
This document details how to deploy CopilotChat's required resources to your Azure subscription.

## Things to know
- Access to Azure OpenAI is currently limited as we navigate high demand, upcoming product improvements, and Microsoft’s commitment to responsible AI. 
  For more details and information on applying for access, go [here](https://learn.microsoft.com/azure/cognitive-services/openai/overview?ocid=AID3051475#how-do-i-get-access-to-azure-openai).
  For regional availability of Azure OpenAI, see the [availability map](https://azure.microsoft.com/explore/global-infrastructure/products-by-region/?products=cognitive-services).
  
- With the limited availability of Azure OpenAI, consider sharing an Azure OpenAI instance across multiple resources.

- `F1` and `D1` SKUs for the App Service Plans are not currently supported for this deployment in order to support private networking.


# Configure your environment
Before you get started, make sure you have the following requirements in place:
- Azure CLI (i.e., az) (if you already installed Azure CLI, make sure to update your installation to the latest version)
  - Windows, go to https://aka.ms/installazurecliwindows
  - Linux, run "`curl -L https://aka.ms/InstallAzureCli | bash`"
- Azure Static Web App CLI (i.e., swa) can be installed by running "`npm install -g @azure/static-web-apps-cli`"
- (Linux only) `zip` can be installed by running "`sudo apt install zip`"


# Deploy Azure Infrastructure
The examples below assume you are using an existing Azure OpenAI resource. See the notes following each command for using OpenAI or creating a new Azure OpenAI resource.

## PowerShell
```powershell
./deploy-azure.ps1 -Subscription {YOUR_SUBSCRIPTION_ID} -DeploymentName {YOUR_DEPLOYMENT_NAME} -AIService {AzureOpenAI or OpenAI} -AIApiKey {YOUR_AI_KEY} -AIEndpoint {YOUR_AZURE_OPENAI_ENDPOINT}
```
  - To use an existing Azure OpenAI resource, set `-AIService` to `AzureOpenAI` and include `-AIApiKey` and `-AIEndpoint`.
  - To deploy a new Azure OpenAI resource, set `-AIService` to `AzureOpenAI` and omit `-AIApiKey` and `-AIEndpoint`.
  - To use an an OpenAI account, set `-AIService` to `OpenAI` and include `-AIApiKey`.

## Bash
```bash
chmod +x ./deploy-azure.sh
./deploy-azure.sh --subscription {YOUR_SUBSCRIPTION_ID} --deployment-name {YOUR_DEPLOYMENT_NAME} --ai-service {AzureOpenAI or OpenAI} --ai-service-key {YOUR_AI_KEY} --ai-endpoint {YOUR_AZURE_OPENAI_ENDPOINT}
```
  - To use an existing Azure OpenAI resource, set `--ai-service` to `AzureOpenAI` and include `--ai-service-key` and `--ai-endpoint`.
  - To deploy a new Azure OpenAI resource, set `--ai-service` to `AzureOpenAI` and omit `--ai-service-key` and `--ai-endpoint`.
  - To use an an OpenAI account, set `--ai-service` to `OpenAI` and include `--ai-service-key`.

## Azure Portal
You can also deploy the infrastructure directly from the Azure Portal by clicking the button below:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fsemantic-kernel%2Fmain%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fdeploy%2Fmain.json)

> This will automatically deploy the most recent release of CopilotChat backend binaries ([link](https://github.com/microsoft/semantic-kernel/releases?q=copilotchat)).

> To find the deployment name when using `Deploy to Azure`, look for a deployment in your resource group that starts with `Microsoft.Template`.


# Deploy Backend (WebAPI)
To deploy the backend, build the deployment package first and deploy it to the Azure resources created above.

## PowerShell
```powershell
./package-webapi.ps1 

./deploy-webapi.ps1 -Subscription {YOUR_SUBSCRIPTION_ID} -ResourceGroupName rg-{YOUR_DEPLOYMENT_NAME} -DeploymentName {YOUR_DEPLOYMENT_NAME}
```

## Bash
```bash
chmod +x ./package-webapi.sh
./package-webapi.sh

chmod +x ./deploy-webapi.sh
./deploy-webapi.sh --subscription {YOUR_SUBSCRIPTION_ID} --resource-group rg-{YOUR_DEPLOYMENT_NAME} --deployment-name {YOUR_DEPLOYMENT_NAME}
```


# Deploy Frontend (WebApp)

## Prerequisites
### App registration (identity)
You will need an Azure Active Directory (AAD) application registration. 
> For details on creating an application registration, go [here](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).
- Select `Single-page application (SPA)` as platform type, and set the redirect URI to `http://localhost:3000`
- Select `Accounts in any organizational directory and personal Microsoft Accounts` as supported account types for this sample.
- Make a note of the `Application (client) ID` from the Azure Portal for use in the `Deploy` below.

### Install Azure's Static Web Apps CLI
```bash
npm install -g @azure/static-web-apps-cli
```

## PowerShell

```powershell

./deploy-webapp.ps1 -Subscription {YOUR_SUBSCRIPTION_ID} -ResourceGroupName rg-{YOUR_DEPLOYMENT_NAME} -DeploymentName {YOUR_DEPLOYMENT_NAME} -ApplicationClientId {YOUR_APPLICATION_ID}
```

## Bash

```bash
./deploy-webapp.sh --subscription {YOUR_SUBSCRIPTION_ID} --resource-group rg-{YOUR_DEPLOYMENT_NAME} --deployment-name {YOUR_DEPLOYMENT_NAME} --application-id {YOUR_APPLICATION_ID}
```

Your CopilotChat application is now deployed!


# Appendix
## Using custom web frontends to access your deployment
Make sure to include your frontend's URL as an allowed origin in your deployment's CORS settings. Otherwise, web browsers will refuse to let JavaScript make calls to your deployment.

To do this, go on the Azure portal, select your Semantic Kernel App Service, then click on "CORS" under the "API" section of the resource menu on the left of the page.
This will get you to the CORS page where you can add your allowed hosts.

## Authorization
All of endpoints (except `/healthz`) require authorization to access.
By default, an API key is required for access which can be found in the `Authorization:ApiKey` configuration setting.
To authorize requests with the API key, add the API key value to a `x-sk-api-key` header in your requests.

To view your CopilotChat API key:
### PowerShell
```powershell
$webApiName = $(az deployment group show --name {DEPLOYMENT_NAME} --resource-group rg-{DEPLOYMENT_NAME} --output json | ConvertFrom-Json).properties.outputs.webapiName.value

($(az webapp config appsettings list --name $webapiName --resource-group rg-{YOUR_DEPLOYMENT_NAME} | ConvertFrom-JSON) | Where-Object -Property name -EQ -Value Authorization:ApiKey).value
```

### Bash
```bash
eval WEB_API_NAME=$(az deployment group show --name $DEPLOYMENT_NAME --resource-group $RESOURCE_GROUP --output json) | jq -r '.properties.outputs.webapiName.value'

$(az webapp config appsettings list --name $WEB_API_NAME --resource-group rg-{YOUR_DEPLOYMENT_NAME} | jq '.[] | select(.name=="Authorization:ApiKey").value')
```

