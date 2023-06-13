# Deploying Copilot Chat
This document details how to deploy CopilotChat's required resources to your Azure subscription.

## Things to know
- Access to Azure OpenAI is currently limited as we navigate high demand, upcoming product improvements, and Microsoft’s commitment to responsible AI. 
  For more details and information on applying for access, go [here](https://learn.microsoft.com/azure/cognitive-services/openai/overview?ocid=AID3051475#how-do-i-get-access-to-azure-openai).
  For regional availability of Azure OpenAI, see the [availability map](https://azure.microsoft.com/explore/global-infrastructure/products-by-region/?products=cognitive-services).
  
- With the limited availability of Azure OpenAI, consider sharing an Azure OpenAI instance across multiple resources.

- `F1` and `D1` SKUs for the App Service Plans are not currently supported for this deployment in order to support private networking.

- Using the resources below, we recommend deploying a single instance of CopilotChat per resource group and not changing the name of the deployment or resources once deployed.
  Virtual networks, subnets, and applications are bound and need to be updated in a proper order when being deleted or modified.
  Deploying an alternate deployment within a resource group that already contains one may lead to resource conflicts.


# Deploy
To use an existing Azure OpenAI resource, run `./deploy-azure.ps1` with `-AIService` set to `AzureOpenAI` and include `-AIApiKey` and `-AIEndpoint`.

To use deploy a new Azure OpenAI resource, run `./deploy-azure.ps1` with `-AIService` set to `AzureOpenAI`, include `-Region`, and omit `-AIApiKey` and `-AIEndpoint`.

To use an an OpenAI account, run `./deploy-azure.ps1` with `-AIService` set to `OpenAI` and include `-AIApiKey`.

## Using an existing Azure OpenAI resource or OpenAI account
## PowerShell
```powershell
./deploy-azure.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID -AIService {AzureOpenAI or OpenAI} -AIApiKey YOUR_AI_KEY -AIEndpoint YOUR_AZURE_OPENAI_ENDPOINT
```
> `-AIEndpoint` is only required when using Azure OpenAI.

## Bash
```bash
chmod +x ./deploy.sh
./deploy.sh --deployment-name YOUR_DEPLOYMENT_NAME --subscription YOUR_SUBSCRIPTION_ID --ai-service {AzureOpenAI or OpenAI} --ai-service-key YOUR_AZURE_OPENAI_KEY --ai-endpoint YOUR_AZURE_OPENAI_ENDPOINT
```
> `--ai-endpoint` is only required when using Azure OpenAI.

## Azure Portal
[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fsemantic-kernel%2Fadrianwyatt%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fdeploy%2Fmain.json)


TODO VERIFY EVERYTHING BELOW THIS LINE


# Verifying the deployment
To make sure your web app service is running, go to <!-- markdown-link-check-disable -->`https://YOUR_INSTANCE_NAME.azurewebsites.net/healthz`<!-- markdown-link-check-enable-->

To get your instance's URL, click on the "Go to resource group" button you see at the end of your deployment. Then click on the resource whose name starts with "app-".

This will bring you to the Overview page on your web service. Your instance's URL is the value that appears next to the "Default domain" field.


# Changing your configuration, monitoring your deployment and troubleshooting
From the page just mentioned in the section above, you can change your configuration by clicking on the "Configuration" item in the "Settings" section of the left pane.

Scrolling down in that same pane to the "Monitoring" section gives you access to a multitude of ways to monitor your deployment.

In addition to this, the "Diagnose and "solve problems" item near the top of the pane can yield crucial insight into some problems your deployment may be experiencing.

If the service itself if functioning properly but you keep getting errors (perhaps reported as 400 HTTP errors) when making calls to the Semantic Kernel,
check that you have correctly entered the values for the following settings:
- AIService:AzureOpenAI
- AIService:Endpoint
- AIService:Models:Completion
- AIService:Models:Embedding
- AIService:Models:Planner

AIService:Endpoint is ignored for OpenAI instances from [openai.com](https://openai.com) but MUST be properly populated when using Azure OpenAI instances.

# Authorization
All of the server's endpoints other than the /healthz one require authorization to access.
By default, the deployment templates set up the server so that an API key is required to access its endpoints.

AAD authentication and authorization can also be set up manually after the automated deployment is done.

To view the API key required by your instance, access the page for your Semantic Kernel app service in the Azure portal.
From that page, click on the "Configuration" item in the "Settings" section of the left pane. Then click on the text that reads "Hidden value.
Click to show value" next to the "Authorization:ApiKey" setting.

To authorize requests with the API key, it must be added as the value of an "x-sk-api-key" header added to the requests.

# Using web frontends to access your deployment
Make sure to include your frontend's URL as an allowed origin in your deployment's CORS settings. Otherwise, web browsers will refuse to let JavaScript make calls to your deployment.

To do this, go on the Azure portal, select your Semantic Kernel App Service, then click on "CORS" under the "API" section of the resource menu on the left of the page.
This will get you to the CORS page where you can add your allowed hosts.

# Deploying your custom version of Semantic Kernel
You can build and upload a customized version of the Semantic Kernel service.

You can use the standard methods available to [deploy an ASP.net web app](https://learn.microsoft.com/en-us/azure/app-service/quickstart-dotnetcore?pivots=development-environment-vs&tabs=net70) in order to do so.

Alternatively, you can follow the steps below to manually build and upload your customized version of the Semantic Kernel service to Azure.

Modify the code to your needs (for example, by adding your own skills). Once that is done, go into the ../semantic-kernel/samples/apps/copilot-chat-app/webapi
directory and enter the following command:
```powershell
dotnet publish CopilotChatWebApi.csproj --configuration Release --arch x64 --os win
```

This will create the following directory, which will contain all the files needed for a deployment:
../semantic-kernel/samples/apps/copilot-chat-app/webapi/bin/Release/net6.0/win-x64/publish

Zip the contents of that directory then put the resulting zip file on the web.

Put its URI in the "Package Uri" field in the web deployment page you access through the "Deploy to Azure" buttons above, or use its URI as the value for the PackageUri parameter of the Powershell scripts above. Make sure that your zip file is publicly readable.

Your deployment will then use your customized deployment package.


# Cleaning up
Once you are done with your resources, you can delete them from the Azure portal. You can also simply delete the resource group in which they are from the portal or through the
following [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) command:
```powershell
az group delete --name YOUR_RESOURCE_GROUP
```