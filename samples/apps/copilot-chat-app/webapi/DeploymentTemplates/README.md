# Deploying Semantic Kernel as a Service

## Things to know

Azure currently limits the number of OpenAI resources per region per subscription to 3. Bearing this in mind, you might want to use the same Azure OpenAI instance for multiple deployments of Semantic Kernel as a Service.

To do so, or to use an OpenAI instance from [openai.com](https://openai.com), use the version of the deployment template that uses existing OpenAI resources.

Either way, you also need to have the necessary permissions to create resources in the target subscription.

Also note that the F1 and D1 App Service SKU's (the Free and Shared ones) are not supported for this deployment.

## Deploying with a new Azure OpenAI instance

Use the [DeploySKaaS.ps1](DeploySKaaS.ps1) file found in this folder:
```powershell
.\DeploySKaaS.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID
```

This will deploy an instance of Semantic Kernel as a Service in a resource group that will bear the name YOUR_DEPLOYMENT_NAME followed by the "-rg" suffix in the specified subscription.

For more options, see the deployment script.

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fglahaye%2Fsemantic-kernel%2Fdeploy%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk.json)

## Deploying with an existing OpenAI / Azure OpenAI instance

Use the [DeploySKaaS-ReUse-AI.ps1](DeploySKaaS-ReUse-AI.ps1) file found in this folder:
```powershell
.\DeploySKaaS-Existing-AI.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID -Endpoint "YOUR_AZURE_OPENAI_ENDPOINT"
```

After entering the command above, you will be prompted to enter your OpenAI or Azure OpenAI API key. (You can also pass in the API key using the -ApiKey paramater followed by a SecureString)

Note: the Azure OpenAI endpoint is ignored and can be omitted when you are using an OpenAI instance from [openai.com](https://openai.com).

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fglahaye%2Fsemantic-kernel%2Fdeploy%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk-existing-ai.json)

## Verifying the deployment

To make sure your instance of Semantic Kernel as a Service is running, go to
https://YOUR_INSTANCE_NAME.azurewebsites.net/probe

To get your instance's URL, click on the "Go to resource group" button you see at the end of your deployment. Then click on the resource whose name ends with "-web". This will bring you to the Overview page on your web service. Your instance's URL is the value that appears next to the "Default domain" field.

## Changing your configuration, monitoring your deployment and troubleshooting

From the page just mentioned in the section above, you can change your configuration by clicking on the "Configuration" item in the "Settings" section of the left pane.

Scrolling down in that same pane to the "Monitoring" section gives you access to a multitude of ways to monitor your deployment.

In addition to this, the "Diagnose and "solve problems" item near the top of the pane can yield crucial insight into some problems your deployment may be experiencing.

If the service itself if functionning properly but you keep getting errors (perhaps reported as 400 HTTP errors) when making calls to the Semantic Kernel, check that you have correctly entered the values for the following settings:
- Completion:AzureOpenAI
- Completion:DeploymentOrModelId
- Completion:Endpoint
- Completion:Label
- Embedding:AzureOpenAI
- Embedding:DeploymentOrModelId
- Embedding:Endpoint
- Embedding:Label

Both Completion:Endpoint and Embedding:Endpoint are ignored for OpenAI instances from [openai.com](https://openai.com) but MUST be properly populated when using Azure OpenAI instances.

## Using web frontends to access your deployment

Make sure to include your frontend's URL as an allowed origin in your deployment's CORS settings. Otherwise, web browsers will refuse to let JavaScript make calls to your deployment.

## Cleaning up

Once you are done with your resources, you can delete them from the Azure portal. You can also simply delete the resource group in which they are from the portal or through the following [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/) command:
```powershell
az group delete --name YOUR_RESOURCE_GROUP
```