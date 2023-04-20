# Copilot Chat Web App

> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

### Watch the Copilot Chat Sample Quick Start Video [here](https://aka.ms/SK-Copilotchat-video).

## Introduction

This chat experience is a chat skill containing multiple functions that work together
to construct the final prompt for each exchange.

The Copilot Chat sample showcases how to build an enriched intelligent app, with
multiple dynamic components, including command messages, user intent, and context.
The chat prompt will evolve as the conversation between user and application proceeds.

## Requirements to run this app

1. Azure Open AI Service Key and working End point. (https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?tabs=command-line&pivots=programming-language-studio)
2. A registered App in Azure Portal (https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
   - Select Single-page application (SPA) as platform type, and the Redirect URI will be `http://localhost:3000`
   - Select **`Accounts in any organizational directory (Any Azure AD directory - Multitenant)
     and personal Microsoft accounts (e.g. Skype, Xbox)`** as the supported account
     type for this sample.
   - Note the **`Application (client) ID`** from your app registration.
3. Yarn - used for installing the app's dependencies (https://yarnpkg.com/getting-started/install)

## Running the sample

1. Ensure the web api is running at `https://localhost:40443/`. See
   [webapi README](../webapi/README.md) for instructions.
2. Create an `.env` file to this folder root with the following variables and fill
   in with your information, where
   `REACT_APP_AAD_CLIENT_ID=` is the GUID copied from the **Application (client) ID**
   from your app registration in the Azure Portal and
   `REACT_APP_BACKEND_URI=` is the URI where your backend is running.

   ```
   REACT_APP_BACKEND_URI=https://localhost:40443/
   REACT_APP_AAD_CLIENT_ID=
   ```

3. **Run** the following command `yarn install` (if you have never run the app before)
   and/or `yarn start` from the command line.
4. A browser will automatically open, otherwise you can navigate to `http://localhost:3000/`
   to use the ChatBot.

### Working with Secrets

We need keys to work with various aspects of the project including accessing OpenAI
models. This opens up the possibility of exposing keys in commits. There are a
[couple of options](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets?view=aspnetcore-7.0&tabs=windows)
to safeguard developers from exposing keys. Outside of using the dotnet's users-secrets
and environment variables, we've also added *.development.json and *.development.config
to the .gitignore if developers want to use appsettings.development.json files or
other development.config files for secret storage.

## AuthN/AuthZ Story
### Authentication in this sample

This sample uses the Microsoft Authentication Library (MSAL) for React to sign in
users. Learn more about it here: https://learn.microsoft.com/en-us/azure/active-directory/develop/tutorial-v2-react.

### Authorizing SKaaS (SK as a Service)
When the user logs in, they will be prompted to consent to scopes set as `skScopes`
in the [Constants.ts file](./src/Constants.ts). These scopes contain some default
OpenID Connect scopes and the `User.Read` scope.

These scopes will authorize the user to access the SK Server (webapi application
you are running on https://localhost:40443/). Each time the kernel is called to
invoke a skill, the WebApp will acquire a token with these scopes to pass to the server.


### Authorizing Connectors used in Semantic Kernel Skills
Some skills utilize [connectors](https://learn.microsoft.com/en-us/semantic-kernel/concepts-sk/connectors)
to allow you to connect to external APIs or services for added functionality. These
skills require separate access tokens to authorize to these external resources.
[useConnectors.ts](./src/libs/connectors/useConnectors.ts) handles this token acquisition.

This sample follows the 'incremental consent' concept, so new permissions will require
additional consent, in which the user will be prompted when a request for the token
is made. If consent is granted and the user is authorized, an access token will be
passed to the server under a new header: `sk-copilot-connector-access-token`.
The `Authorization` header is reserved for the SKaaS Access token.

To invoke skills with the required tokens, do the following (see comments tagged
`ConnectorTokenExample` in [useChat](./src/libs/useChat.ts) for example):

1. Import the Connectors hook: `import { useConnectors } from '{path}/connectors/useConnectors';`
2. In component: `const connectors = useConnectors();`
3. Invoke Skill with scopes required for the downstream Connector as an array, i.e. `const scopes = ['User.Read']`

   `var result = await connectors.invokeSkillWithConnectorToken(ask, {ConnectorSkill}, {ConnectorFunction}, scopes);`

      - To use Graph token specifically, uncomment the scopes you need under `msGraphScopes`
        in [Constants.ts file](./src/Constants.ts), then call the `invokeSkillWithGraphToken`
        function. Be default, the ones already uncommented map to Graph APIs used in existing connectors.
      
        i.e., `var result = await connectors.invokeSkillWithGraphToken(ask, {ConnectorSkill}, {ConnectorFunction});`

      - To use ADO token specifically, uncomment the scopes you need under `adoScopes`
        in [Constants.ts file](./src/Constants.ts), then call the `invokeSkillWithAdoToken`
        function.
      
        i.e., `var result = await connectors.invokeSkillWithAdoToken(ask, {ConnectorSkill}, {ConnectorFunction});`
4. Process result as normal.

## Debug the web app
Aside from debugging within browsers, you can launch VSCode debug session in VSCode. Here are the instructions:
1. Make sure VSCode opened the webapp folder (`REPO_ROOT\samples\apps\copilot-chat-app\WebApp`).
2. In VSCode, go to "Run and Debug", and select on the "Launch Edge against localhost" from the "RUN and DEBUG" dropdown menu. Click [here](https://code.visualstudio.com/docs/typescript/typescript-debugging) to learn more about debug client-code with VSCode.