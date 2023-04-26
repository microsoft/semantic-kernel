# Deploying Semantic Kernel as a Service

## Things to know

Azure currently limits the number of OpenAI resources per region per Azure subscription to 3. Bearing this in mind, you might want to use the same Azure OpenAI instance for multiple deployments of Semantic Kernel as a Service.

To do so, or to use an OpenAI instance from [openai.com](https://openai.com), use the version of the deployment template that uses existing OpenAI resources.

## Deploying with a new Azure OpenAI instance

Use the [DeploySKaaS.ps1](DeploySKaaS.ps1) file found in this folder:
```powershell
.\DeploySKaaS.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID
```

This will deploy an instance of Semantic Kernel as a Service in a resource group that will bear the name YOUR_DEPLOYMENT_NAME followed by the "-rg" suffix in the specified subscription.

For more options, see the deployment script.

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fglahaye%2Fsemantic-kernel%2Fdeploy%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk.json)

## Deploying with an existing OpenAI instance

Use the [DeploySKaaS-ReUse-AI.ps1](DeploySKaaS-ReUse-AI.ps1) file found in this folder:
```powershell
.\DeploySKaaS-ReUse-AI.ps1 -DeploymentName YOUR_DEPLOYMENT_NAME -Subscription YOUR_SUBSCRIPTION_ID -Endpoint "YOUR_AZURE_OPENAI_ENDPOINT"
```

Note: don't provide the Azure OpenAI endpoint if you are using an OpenAI instance from [openai.com](https://openai.com).

Alternatively, you can deploy by clicking on the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fglahaye%2Fsemantic-kernel%2Fdeploy%2Fsamples%2Fapps%2Fcopilot-chat-app%2Fwebapi%2FDeploymentTemplates%2Fsk-existing-ai.json)

## Verifying the deployment

To make sure your instance of Semantic Kernel as a Service is running, go to
https://YOUR_INSTANCES_NAME.azurewebsites.net/probe

## Using web front ends to access your deployment

Make sure to include your front end's URL as an allowed origin in your deployment's CORS settings. Otherwise, web browsers will refuse to let JavaScript make call to your deployment.