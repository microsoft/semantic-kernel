# Copilot Chat Web App
> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

## Introduction
This chat experience is a chat skill containing multiple functions that work together to construct the final prompt for each exchange.

The Copilot Chat sameple showcases how to build an enriched intelligent app, with multiple dynamic components, including command messages, user intent, and context.  The chat prompt will evolve as the conversation between user and application proceeds. 
     
### Watch the Copilot Chat Sample Quick Start Video [here](https://aka.ms/SK-Copilotchat-video).

## Requirements to run this app
1. Azure Open AI Service Key and working End point. (https://learn.microsoft.com/en-us/azure/cognitive-services/openai/quickstart?tabs=command-line&pivots=programming-language-studio)
2.	A registered App in Azure Portal (https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
   -	Select Single-page application (SPA) as platform type, and the Redirect URI will be https://localhost:3000
   - Select **`Accounts in this organizational directory only`** as the supported account type for this sample.
   - Note the `Application (client) ID` and `Directory (tenant) ID` from the app registration.
3.	Yarn - used for installing the app's dependencies (https://yarnpkg.com/getting-started/install)

## Running the sample

1. Ensure the SKWebApi running at `https://localhost:40443`
2. Create an **[.env](.env)** file to this folder root with the following variables and fill in with your information, where
   `REACT_APP_CHAT_CLIENT_ID=` is the GUID copied from the **Application (client) ID** from your app registration in the Azure Portal, 
   `REACT_APP_BACKEND_URI=` is the URI where your backend is running, and `REACT_APP_TENANT_ID` is your tenant ID. 
      
      REACT_APP_BACKEND_URI=https://localhost:40443
      REACT_APP_CHAT_CLIENT_ID=
      REACT_APP_TENANT_ID=

3. **Run** the following command `yarn install` (if you have never run the app before) and/or `yarn start` from the command line.
4. A browser will automatically open, otherwise you can navigate to `http://localhost:3000/` to use the ChatBot.

## Authentication in this sample
This sample uses the Microsoft Authentication Library (MSAL) for React to sign in users. Learn more about it here: https://learn.microsoft.com/en-us/azure/active-directory/develop/tutorial-v2-react.