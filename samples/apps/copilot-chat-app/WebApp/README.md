# Copilot Chat Web App

> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

### Watch the Copilot Chat Sample Quick Start Video [here](https://aka.ms/SK-Copilotchat-video).

## Introduction

This chat experience is a chat skill containing multiple functions that work together to construct the final prompt for each exchange.

The Copilot Chat sameple showcases how to build an enriched intelligent app, with multiple dynamic components, including command messages, user intent, and context. The chat prompt will evolve as the conversation between user and application proceeds.

## Requirements to run this app

1. Azure Open AI Service Key and working End point. (https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?tabs=command-line&pivots=programming-language-studio)
2. A registered App in Azure Portal (https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
   - Select Single-page application (SPA) as platform type, and the Redirect URI will be `http://localhost:3000`
   - Select **`Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)`** as the supported account type for this sample.
   - Note the **`Application (client) ID`** from your app registration.
3. Yarn - used for installing the app's dependencies (https://yarnpkg.com/getting-started/install)

## Running the sample

1. Ensure the web api is running at `https://localhost:40443/`. See [webapi README](../webapi/README.md) for instructions.
2. Create an `.env` file to this folder root with the following variables and fill in with your information, where
   `REACT_APP_AAD_CLIENT_ID=` is the GUID copied from the **Application (client) ID** from your app registration in the Azure Portal and
   `REACT_APP_BACKEND_URI=` is the URI where your backend is running.

   ```
   REACT_APP_BACKEND_URI=https://localhost:40443/
   REACT_APP_AAD_CLIENT_ID=
   ```

3. **Run** the following command `yarn install` (if you have never run the app before) and/or `yarn start` from the command line.
4. A browser will automatically open, otherwise you can navigate to `http://localhost:3000/` to use the ChatBot.

### Working with Secrets

We need keys to work with various aspects of the project including accessing openAI models. This opens up the possibility of exposing keys in commits. There are a [couple of options](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets?view=aspnetcore-7.0&tabs=windows) to safeguard developers from exposing keys. Outside of using the dotnet's users-secrets and environment variables, we've also added *.development.json and *.development.config to the .gitignore if developers want to use appsettings.development.json files or other development.config files for secret storage.

## Authentication in this sample

This sample uses the Microsoft Authentication Library (MSAL) for React to sign in users. Learn more about it here: https://learn.microsoft.com/en-us/azure/active-directory/develop/tutorial-v2-react.
