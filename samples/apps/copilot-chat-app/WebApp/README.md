# Copilot Chat Web App
> **!IMPORTANT**
> This learning sample is for educational purposes only and should not be used in any
> production use case. It is intended to highlight concepts of Semantic Kernel and not
> any architectural / security design practices to be used.

The Copilot Chat sample showcases how you can create an enriched experience with multiple dynamic components, including command messages, user intent, and memories, etc. The chat prompt will evolve as the conversation between the user and the application proceeds. This chat experience is a chat skill containing multiple functions that work together to construct the final prompt for each exchange.  
     
### Watch the Copilot Chat Sample Quick Start Video [here](https://aka.ms/SK-Copilotchat-video).

## Running the sample

1. Ensure the SKWebApi running at `https://localhost:40443` (or whichever host and port you chose)
3. You will also need to
   [register your application](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app)
   in the Azure Portal. Follow the steps to register your app
   [here](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app).
    - Select **`Single-page application (SPA)`** as platform type, and the Redirect URI will be **`http://localhost:3000`**
    - Select **`Accounts in any organizational directory and personal Microsoft accounts`** as supported account types for this sample.
4. Create an **[.env](.env)** file to this folder root with the following variables and fill in with your information, where
   `APP_CHAT_CLIENT_ID=` is the GUID copied from the **Application (client) ID** from the Azure Portal and
   `APP_BACKEND_URI=` is the URI where your backend is running:
        
        APP_CHAT_CLIENT_ID=
        APP_BACKEND_URI=http://localhost:40443

5. **Run** the following command `yarn install` (if you have never run the app before)
   and/or `yarn start` from the command line.
6. A browser will automatically open, otherwise you can navigate to `http://localhost:3000/` to use the ChatBot.

## About the Copilot Chat Sample

### Authentication in this sample
This sample uses the Microsoft Authentication Library (MSAL) for React to sign in users. Learn more about it here: https://learn.microsoft.com/en-us/azure/active-directory/develop/tutorial-v2-react.