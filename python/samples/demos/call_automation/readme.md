# Call Automation - Quick Start Sample

This is a sample application. It highlights an integration of Azure Communication Services with Semantic Kernel, using the Azure OpenAI Service to enable intelligent conversational agents.

Original code for this sample can be found [here](https://github.com/Azure-Samples/communication-services-python-quickstarts/tree/main/callautomation-openai-sample).

## Prerequisites

- An Azure account with an active subscription. [Create an account for free](https://azure.microsoft.com/free/?WT.mc_id=A261C142F).
- A deployed Communication Services resource. [Create a Communication Services resource](https://docs.microsoft.com/azure/communication-services/quickstarts/create-communication-resource).
- A [phone number](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number) in your Azure Communication Services resource that can get inbound calls. NB: phone numbers are not available in free subscriptions.
- [Python](https://www.python.org/downloads/) 3.9 or above.
- An Azure OpenAI Resource and Deployed Model. See [instructions](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal).
- Install `uv`, see [the uv docs](https://docs.astral.sh/uv/getting-started/installation/).

## To run the app

1. Open an instance of PowerShell, Windows Terminal, Command Prompt or equivalent and navigate to the directory that you would like to clone the sample to.
2. git clone `https://github.com/microsoft/semantic-kernel.git`.
3. Navigate to `python/samples/demos/call_automation` folder

### Setup and host your Azure DevTunnel

[Azure DevTunnels](https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/overview) is an Azure service that enables you to share local web services hosted on the internet. Use the commands below to connect your local development environment to the public internet. This creates a tunnel with a persistent endpoint URL and which allows anonymous access. We will then use this endpoint to notify your application of calling events from the ACS Call Automation service.

```bash
devtunnel create --allow-anonymous
devtunnel port create -p 8080
devtunnel host
```

### Configuring application

Copy the `.env.example` file to `.env` and update the following values:

1. `ACS_CONNECTION_STRING`: Azure Communication Service resource's connection string.
2. `CALLBACK_URI_HOST`: Base url of the app. (For local development use the dev tunnel url from the step above)
3. `AZURE_OPENAI_ENDPOINT`: Azure Open AI service endpoint
4. `AZURE_OPENAI_REALTIME_DEPLOYMENT_NAME`: Azure Open AI deployment name
5. `AZURE_OPENAI_API_VERSION`: Azure Open AI API version, this should be one that includes the realtime api, for instance '2024-10-01-preview'
6. `AZURE_OPENAI_API_KEY`: Azure Open AI API key, optionally, you can also use Entra Auth.

## Run the app

1. Navigate to `call_automation` folder and do one of the following to start the main application:
   - run `call_automation.py` in debug mode from your IDE (VSCode will load your .env variables into the environment automatically, other IDE's might need an extra step).
   - execute `uv run --env-file .env call_automation.py` directly in your terminal (this uses `uv`, which will then install the requirements in a temporary virtual environment, see [uv docs](https://docs.astral.sh/uv/guides/scripts) for more info).
2. Browser should pop up with a simple page. If not navigate it to `http://localhost:8080/` or your dev tunnel url.
3. Register an EventGrid Webhook for the IncomingCall(`https://<devtunnelurl>/api/incomingCall`) event that points to your devtunnel URI. Instructions [here](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/incoming-call-notification).

Once that's completed you should have a running application. The way to test this is to place a call to your ACS phone number and talk to your intelligent agent!

In the terminal you should see all sorts of logs from both ACS and Semantic Kernel.
