# Deploying Semantic Kernel to Azure in a web app service


## Things to know

Azure currently limits the number of OpenAI resources per region per subscription to 3. Also, OpenAI is not available in every region.
(Refer to this [availability map](https://azure.microsoft.com/en-us/explore/global-infrastructure/products-by-region/?products=cognitive-services))
Bearing this in mind, you might want to use the same Azure OpenAI instance for multiple deployments of Semantic Kernel to Azure.

To do so, or to use an OpenAI instance from [openai.com](https://openai.com), use one of the versions of the deployment template that uses existing OpenAI resources.

Either way, you also need to have the necessary permissions to create resources in the target subscription.

Also note that the F1 and D1 App Service SKU's (the Free and Shared ones) are not supported for this deployment.


## Deploying with a new Azure OpenAI instance

You can deploy an instance of Semantic Kernel in a web app service within a resource group that bears the name YOUR_DEPLOYMENT_NAME preceded by the "rg-" prefix using any of the following methods.

### PowerShell

Use the [DeploySK.ps1](DeploySK.ps1) file found in this folder:
```powershell
.\DeploySK.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID
```

For more options, see the deployment script.

### Bash

After ensuring DeploySK.sh file found in this folder is executable, enter the following command:

```bash
./DeploySK.sh -d DEPLOYMENT_NAME -s SUBSCRIPTION_ID
```

### Azure Portal

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fsemantic-kernel%2Fmain%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk-new.json)


## Deploying with an existing Azure OpenAI account

### PowerShell

Use the [DeploySK-Existing-AzureOpenAI.ps1](DeploySK-Existing-AzureOpenAI.ps1) file found in this folder:
```powershell
.\DeploySK-Existing-AzureOpenAI.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID -Endpoint "YOUR_AZURE_OPENAI_ENDPOINT"
```

After entering the command above, you will be prompted to enter your Azure OpenAI API key. (You can also pass in the API key using the -ApiKey parameter)

### Bash

After ensuring the [DeploySK-Existing-AzureOpenAI.sh](DeploySK-Existing-AzureOpenAI.sh) file found in this folder is executable, enter the following command:

```bash
./DeploySK-Existing-AzureOpenAI.sh -d YOUR_DEPLOYMENT_NAME -s YOUR_SUBSCRIPTION_ID -e "YOUR_AZURE_OPENAI_ENDPOINT" -o YOUR_AZURE_OPENAI_API_KEY
```

### Azure Portal

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fsemantic-kernel%2Fmain%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk-existing-azureopenai.json)


## Deploying with an existing account from openai.com

### PowerShell

Use the [DeploySK-Existing-OpenAI.ps1](DeploySK-Existing-OpenAI.ps1) file found in this folder:
```powershell
.\DeploySK-Existing-OpenAI.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID
```

After entering the command above, you will be prompted to enter your OpenAI API key. (You can also pass in the API key using the -ApiKey parameter)

### Bash

After ensuring DeploySK-Existing-OpenAI.sh file found in this folder is executable, enter the following command:

```bash
./DeploySK-Existing-AI.sh -d YOUR_DEPLOYMENT_NAME -s YOUR_SUBSCRIPTION_ID -o YOUR_OPENAI_API_KEY
```

### Azure Portal

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fmicrosoft%2Fsemantic-kernel%2Fmain%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk-existing-openai.json)


## Verifying the deployment

To make sure your web app service is running, go to <!-- markdown-link-check-disable -->https://YOUR_INSTANCE_NAME.azurewebsites.net/probe<!-- markdown-link-check-enable-->

To get your instance's URL, click on the "Go to resource group" button you see at the end of your deployment. Then click on the resource whose name starts with "app-".

This will bring you to the Overview page on your web service. Your instance's URL is the value that appears next to the "Default domain" field.


## Changing your configuration, monitoring your deployment and troubleshooting

From the page just mentioned in the section above, you can change your configuration by clicking on the "Configuration" item in the "Settings" section of the left pane.

Scrolling down in that same pane to the "Monitoring" section gives you access to a multitude of ways to monitor your deployment.

In addition to this, the "Diagnose and "solve problems" item near the top of the pane can yield crucial insight into some problems your deployment may be experiencing.

If the service itself if functioning properly but you keep getting errors (perhaps reported as 400 HTTP errors) when making calls to the Semantic Kernel,
check that you have correctly entered the values for the following settings:
- AIService:AzureOpenAI
- AIService:Endpoint

Both Completion:Endpoint and Embedding:Endpoint are ignored for OpenAI instances from [openai.com](https://openai.com) but MUST be properly populated when using Azure OpenAI instances.


## Authorization

All of the server's endpoints other than the /probe one require authorization to access.
By default, the deployment templates set up the server so that an API key is required to access its endpoints.

AAD authentication and authorization can also be set up manually after the automated deployment is done.

To view the API key required by your instance, access the page for your Semantic Kernel app service in the Azure portal.
From that page, click on the "Configuration" item in the "Settings" section of the left pane. Then click on the text that reads "Hidden value.
Click to show value" next to the "Authorization:ApiKey" setting.

To authorize requests with the API key, it must be added as the value of an "x-sk-api-key" header added to the requests.


## Using web frontends to access your deployment

Make sure to include your frontend's URL as an allowed origin in your deployment's CORS settings. Otherwise, web browsers will refuse to let JavaScript make calls to your deployment.

To do this, go on the Azure portal, select your Semantic Kernel App Service, then click on "CORS" under the "API" section of the resource menu on the left of the page.
This will get you to the CORS page where you can add your allowed hosts.


## Deploying your custom version of Semantic Kernel

You can build and upload a customized version of the Semantic Kernel service.

To do so, clone the code from this repo then modify it to your needs (for example, by adding your own skills). Once that is done, go into the ../semantic-kernel/samples/apps/copilot-chat-app/webapi
directory and enter the following command:
```powershell
dotnet publish CopilotChatApi.csproj --configuration Release --arch x64 --os win
```

This will create the following directory, which will contain all the files needed for a deployment:
../semantic-kernel/samples/apps/copilot-chat-app/webapi/bin/Release/net6.0/win-x64/publish

Zip the contents of that directory then put the resulting zip file on the web.

Put its URI in the "Package Uri" field in the web deployment page you access through the "Deploy to Azure" buttons above, or use its URI as the value for the PackageUri parameter of the Powershell scripts above.

Your deployment will then use your customized deployment package.


## Cleaning up

Once you are done with your resources, you can delete them from the Azure portal. You can also simply delete the resource group in which they are from the portal or through the
following [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) command:
```powershell
az group delete --name YOUR_RESOURCE_GROUP
```