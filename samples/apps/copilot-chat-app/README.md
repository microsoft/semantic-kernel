# Copilot Chat Sample Application

> This sample is for educational purposes only and is not recommended for production deployments.

# About Copilot Chat

This sample allows you to build your own integrated large language model chat copilot.
This is an enriched intelligence app, with multiple dynamic components including
command messages, user intent, and memories.

The chat prompt and response will evolve as the conversation between the user and the application proceeds.
This chat experience is orchestrated with Semantic Kernel and a Copilot Chat skill containing numerous
functions that work together to construct each response.

![UI Sample](images/UI-Sample.png)

# Automated Setup and Local Deployment

Refer to [./scripts/README.md](./scripts/README.md) for local configuration and deployment.

Refer to [./deploy/README.md](./deploy/README.md) for Azure configuration and deployment.

# Manual Setup and Local Deployment

## Configure your environment

Before you get started, make sure you have the following requirements in place:

- [.NET 6.0 SDK](https://dotnet.microsoft.com/download/dotnet/6.0)
- [Node.js](https://nodejs.org/)
- [Yarn](https://classic.yarnpkg.com/lang/en/docs/install) - After installation, run `yarn --version` in a terminal window to ensure you are running v1.22.19.
- [Azure OpenAI](https://aka.ms/oai/access) resource or an account with [OpenAI](https://platform.openai.com).
- [Visual Studio Code](https://code.visualstudio.com/Download) **(Optional)** 

## Start the WebApi Backend Server

The sample uses two applications, a front-end web UI, and a back-end API server.
First, let’s set up and verify the back-end API server is running.

1. Generate and trust a localhost developer certificate. Open a terminal and run:
   - For Windows and Mac run `dotnet dev-certs https --trust` and select `Yes` when asked if you want to install this certificate.
   - For Linux run `dotnet dev-certs https`
   > **Note:** It is recommended you close all instances of your web browser after installing the developer certificates.

2. Navigate to `samples/apps/copilot-chat-app/webapi` and open `appsettings.json`
   - Update the `AIService` configuration section:
     - Update `Type` to the AI service you will be using (i.e., `AzureOpenAI` or `OpenAI`).
     - If your are using Azure OpenAI, update `Endpoint` to your Azure OpenAI resource Endpoint address (e.g.,
       `http://contoso.openai.azure.com`).
        > If you are using OpenAI, this property will be ignored.
     - Set your Azure OpenAI or OpenAI key by opening a terminal in the webapi project directory and using `dotnet user-secrets`
       ```bash
       cd semantic-kernel/samples/apps/copilot-chat-app/webapi
       dotnet user-secrets set "AIService:Key" "MY_AZUREOPENAI_OR_OPENAI_KEY"
       ```
     - **(Optional)** Update `Models` to the Azure OpenAI deployment or OpenAI models you want to use. 
       - For `Completion` and `Planner`, CopilotChat is optimized for Chat completion models, such as gpt-3.5-turbo and gpt-4.
         > **Important:** gpt-3.5-turbo is normally labelled as "`gpt-35-turbo`" (no period) in Azure OpenAI and "`gpt-3.5-turbo`" (with a period) in OpenAI.
       - For `Embedding`, `text-embedding-ada-002` is sufficient and cost-effective for generating embeddings.
       > **Important:** If you are using Azure OpenAI, please use [deployment names](https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource). If you are using OpenAI, please use [model names](https://platform.openai.com/docs/models).
   
   - **(Optional)** To enable speech-to-text for chat input, update the `AzureSpeech` configuration section:
     > If you have not already, you will need to [create an Azure Speech resource](https://ms.portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices)
       (see [./webapi/appsettings.json](webapi/appsettings.json) for more details).
     - Update `Region` to whichever region is appropriate for your speech sdk instance.
     - Set your Azure speech key by opening a terminal in the webapi project directory and setting
       a dotnet user-secrets value for `AzureSpeech:Key`
       ```bash
       dotnet user-secrets set "AzureSpeech:Key" "MY_AZURE_SPEECH_KEY" 
       ```

3. Build and run the back-end API server
    1. Open a terminal and navigate to `samples/apps/copilot-chat-app/webapi`
    
    2. Run `dotnet build` to build the project.
    
    3. Run `dotnet run` to start the server.
    
    4. Verify the back-end server is responding, open a web browser and navigate to `https://localhost:40443/healthz`
       > The first time accessing the probe you may get a warning saying that there is a problem with website's certificate.
         Select the option to accept/continue - this is expected when running a service on `localhost`
         It is important to do this, as your browser may need to accept the certificate before allowing the frontend to communicate with the backend.

      > You may also need to acknowledge the Windows Defender Firewall, and allow the app to communicate over private or public networks as appropriate.

## Start the WebApp FrontEnd application

1. Build and start the front-end application
   1. You will need an Azure Active Directory (AAD) application registration. 
      > For more details on creating an application registration, go [here](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).
      - Select `Single-page application (SPA)` as platform type, and set the Web redirect URI to `http://localhost:3000`
      - Select `Accounts in any organizational directory and personal Microsoft Accounts` as supported account types for this sample.
      - Make a note of the `Application (client) ID` from the Azure Portal, we will use of it later.

   2. Open a terminal and navigate to `samples/apps/copilot-chat-app/webapp` Copy `.env.example` into a new
      file `.env` and update the `REACT_APP_AAD_CLIENT_ID` with the AAD application (Client) ID created above.
      For example:
      ```bash
      REACT_APP_BACKEND_URI=https://localhost:40443/
      REACT_APP_AAD_CLIENT_ID={Your Application (client) ID}
      REACT_APP_AAD_AUTHORITY=https://login.microsoftonline.com/common
      ```
      > For more detail on AAD authorities, see [Client Application Configuration Authorities](https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-client-application-configuration#authority).

      > `REACT_APP_SK_API_KEY` is only required if you're using an Semantic Kernel service deployed to Azure. See the [Authorization section of Deploying Semantic Kernel to Azure in a web app service](./deploy/README.md#authorization) for more details and instruction on how to find your API key.
      ```bash
      REACT_APP_SK_API_KEY={Your API Key, should be the same as Authorization:ApiKey from appsettings.json}
      ```

   3. To build and run the front-end application, open a terminal and navigate to `samples/apps/copilot-chat-app/webapp` if not already, then run:
      ```bash
      yarn install
      yarn start
      ```
      > To run the WebApp with HTTPs, see [How to use HTTPS for local development](./webapp/README.md#how-to-use-https-for-local-development).

   4. With the back end and front end running, your web browser should automatically launch and navigate to `http://localhost:3000`
      > The first time running the front-end application may take a minute or so to start.
   
   5. Sign in with a Microsoft personal account or a "Work or School" account.
   
   6. Consent permission for the application to read your profile information (i.e., your name).
    
    If you you experience any errors or issues, consult the troubleshooting section below.

2. Have fun!
   > **Note:** Each chat interaction will call Azure OpenAI/OpenAI which will use tokens that you may be billed for.

# Troubleshooting

## 1. Unable to load chats. Details: interaction_in_progress: Interaction is currently in progress. 

The WebApp can display this error when the application is configured for an active directory tenant,
(e.g., personal/MSA accounts) and the browser attempts to use single sign-on with an account from
another tenant (e.g., work or school account). Either user a private/incognito browser tab or clear
your browser credentials/cookies.

## 2. Issues using text completion models, such as `text-davinci-003`

CopilotChat supports chat completion models, such as `gpt-3.5-*` and `gpt-4-*`.
See [OpenAI's model compatibility](https://platform.openai.com/docs/models/model-endpoint-compatibility) for
the complete list of current models supporting chat completions.

## 3. Localhost SSL certificate errors / CORS errors

![](images/Cert-Issue.png)

If you are stopped at an error message similar to the one above, your browser may be blocking the front-end access
to the back end while waiting for your permission to connect. To resolve this, try the following:

1. Confirm the backend service is running by opening a web browser, and navigating to `https://localhost:40443/healthz`
   - You should see a confirmation message: `Healthy`
2. If your browser asks you to acknowledge the risks of visiting an insecure website, you must acknowledge the
   message before the front end will be allowed to connect to the back-end server. 
   - Acknowledge, continue, and navigate until you see the message `Healthy`.
3. Navigate to `http://localhost:3000` or refresh the page to use the Copilot Chat application.

## 4. Have Yarn version 2.x or 3.x

The webapp uses packages that are only supported by classic Yarn (v1.x). If you have Yarn v2.x+, run
the following commands in your preferred shell to flip Yarn to the classic version.

```shell
npm install -g yarn
yarn set version classic
```

You can confirm the active Yarn version by running `yarn --version`.

# Additional resources

1. [Import Document Application](./importdocument/README.md): Import a document to the memory store.
