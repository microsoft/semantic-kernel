# Copilot Chat Web App

## Running the sample

1. You will need an
   [Azure Open AI Service key and endpoint](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart)
   for this sample
2. Ensure the KernelHttpServer sample is already running at `http://localhost:7071`. If not, follow the steps 
   to start it [here](../../dotnet/KernelHttpServer/README.md).
3. You will also need to
   [register your application](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app)
   in the Azure Portal. Follow the steps to register your app
   [here](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app).
    - Select **`Single-page application (SPA)`** as platform type, and the Redirect URI will be **`https://localhost:3000`**
    - Select **`Personal Microsoft accounts only`** as supported account types for this sample
4. Create an **[.env](.env)** file to this folder root with the following variables and fill in with your information, where `REACT_APP_GRAPH_CLIENT_ID=` is the GUID copied from the **Application (client) ID** from the Azure Portal:
        
        VITE_REACT_APP_CHAT_CLIENT_ID=
        VITE_REACT_APP_FUNCTION_URI=http://localhost:7071
        VITE_REACT_APP_AZURE_OPEN_AI_KEY=
        VITE_REACT_APP_AZURE_OPEN_AI_COMPLETION_DEPLOYMENT=
        VITE_REACT_APP_AZURE_OPEN_AI_EMBEDDINGS_DEPLOYMENT=
        VITE_REACT_APP_AZURE_OPEN_AI_ENDPOINT=

5. **Run** the following command `yarn install` (if you have never run the app before)
   and/or `yarn start` from the command line.
6. A browser will automatically open, otherwise you can navigate to `https://localhost:3000/` to use the ChatBot.