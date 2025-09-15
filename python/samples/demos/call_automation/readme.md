# Call Automation - Quick Start Sample

This is a sample application. It highlights an integration of Azure Communication Services with Semantic Kernel, using the Azure OpenAI Service to enable intelligent conversational agents.

Original code for this sample can be found [here](https://github.com/Azure-Samples/communication-services-python-quickstarts/tree/main/callautomation-openai-sample).

## Prerequisites

- An Azure account with an active subscription. [Create an account for free](https://azure.microsoft.com/free/?WT.mc_id=A261C142F).
- A deployed Communication Services resource. [Create a Communication Services resource](https://docs.microsoft.com/azure/communication-services/quickstarts/create-communication-resource).
- A [phone number](https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number) in your Azure Communication Services resource that can get inbound calls. NOTE: although trial phone numbers are available in free subscriptions, they will not work properly. You must have a paid phone number.
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
2. `CALLBACK_URI_HOST`: Base url of the app. (For local development use the dev tunnel url from the step above). This URI is in the form of `https://<unique-id>-8080.XXXX.devtunnels.ms`.
3. `AZURE_OPENAI_ENDPOINT`: Azure Open AI service endpoint
4. `AZURE_OPENAI_REALTIME_DEPLOYMENT_NAME`: Azure Open AI deployment name
5. `AZURE_OPENAI_API_VERSION`: Azure Open AI API version, this should be one that includes the realtime api, for instance '2024-10-01-preview'. This API version is the currently the only supported version.
6. `AZURE_OPENAI_API_KEY`: Azure Open AI API key, optionally, you can also use Entra Auth.

## Run the app

1. Navigate to `call_automation` folder and do one of the following to start the main application:
   - run `call_automation.py` in debug mode from your IDE (VSCode will load your .env variables into the environment automatically, other IDE's might need an extra step).
   - execute `uv run --env-file .env call_automation.py` directly in your terminal (this uses `uv`, which will then install the requirements in a temporary virtual environment, see [uv docs](https://docs.astral.sh/uv/guides/scripts) for more info).
2. Browser should pop up with a simple page. If not navigate it to `http://localhost:8080/` or your dev tunnel url.
3. Register an EventGrid Webhook for the IncomingCall(`https://<devtunnelurl>/api/incomingCall`) event that points to your devtunnel URI. Instructions [here](https://learn.microsoft.com/en-us/azure/communication-services/concepts/call-automation/incoming-call-notification).
  - To register the event, navigate to your ACS resource in the Azure Portal (follow the Microsoft Learn Docs if you prefer to use the CLI). 
  - On the left menu bar click "Events."
  - Click on "+Event Subscription."
    - Provide a unique name for the event subscription details, for example, "IncomingCallWebhook"
    - Leave the "Event Schema" as "Event Grid Schema"
    - Provide a unique "System Topic Name"
    - For the "Event Types" select "Incoming Call"
    - For the "Endpoint Details" select "Webhook" from the drop down
      - Once "Webhook" is selected, you will need to configure the URI for the incoming call webhook, as mentioned above: `https://<devtunnelurl>/api/incomingCall`.
    - **Important**: before clicking on "Create" to create the event subscription, the `call_automation.py` script must be running, as well as your devtunnel. ACS sends a verification payload to the app to make sure that the communication is configured properly. The event subscription will not succeed in the portal without the script running. If you see an error, this is most likely the root cause.


Once that's completed you should have a running application. The way to test this is to place a call to your ACS phone number and talk to your intelligent agent!

In the terminal you should see all sorts of logs from both ACS and Semantic Kernel. Successful logs can look like the following:

```bash
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: incoming call handler caller id: +14255551234
[2YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: callback url: https://<devtunnelurl>/api/callbacks/<guid>?callerId=%2B14257059063
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: websocket url: wss://<devtunnelurl>/ws
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Answered call for connection id: <guid>>
[YYYY-MM-DD HH:MM:SS,mmm] [28438] [INFO] 127.0.0.1:55481 POST /api/incomingCall 1.1 200 - 595851
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Client connected to WebSocket
[YYYY-MM-DD HH:MM:SS,mmm] [28438] [INFO] 127.0.0.1:55483 GET /ws 1.1 101 - 1262939
Session Created Message
  Session Id: sess_BG0CBnM6CMEGSbpsK5CiC
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Received Event:-> Microsoft.Communication.ParticipantsUpdated, Correlation Id:-> <guid>, CallConnectionId:-> <guid>
[YYYY-MM-DD HH:MM:SS,mmm] [28438] [INFO] 127.0.0.1:55486 POST /api/callbacks/1629809d 1.1 200 - 1642
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Received Event:-> Microsoft.Communication.CallConnected, Correlation Id:-> <guid>, CallConnectionId:-> <guid>
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Received Event:-> Microsoft.Communication.MediaStreamingStarted, Correlation Id:-> <guid>, CallConnectionId:-> <guid>
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Media streaming content type:--> Audio
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Media streaming status:--> mediaStreamingStarted
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Media streaming status details:--> subscriptionStarted
[YYYY-MM-DD HH:MM:SS,mmm] [28438] [INFO] 127.0.0.1:55488 POST /api/callbacks/1629809d 1.1 200 - 1490
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: MediaStreamingSubscription:--> {'additional_properties': {}, 'id': '50a8ca48', 'state': 'active', 'subscribed_content_types': ['audio']}
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: Received CallConnected event for connection id: <guid>
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: CORRELATION ID:--> <guid>
[YYYY-MM-DD HH:MM:SS,mmm] INFO in call_automation: CALL CONNECTION ID:--> <guid>
[YYYY-MM-DD HH:MM:SS,mmm] [28438] [INFO] 127.0.0.1:55487 POST /api/callbacks/1629809d 1.1 200 - 137171
 AI:-- Ah, greetings, dear traveler of the world! In this moment, amidst the tapestry of time and space, you seek a glimpse of the weather that graces a particular place. Pray, tell me, to which location do you wish to turn your gaze, so I might summon the winds and the skies to unfold their secrets for you?
Response Done Message
  Response Id: resp_BG0CBedSOZgrlo82IlxMC
```
