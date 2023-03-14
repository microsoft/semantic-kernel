# Authenticated API’s Sample Learning App

> [!IMPORTANT]
> This learning sample is for educational purposes only and should not be used in any production
> use case. It is intended to highlight concepts of Semantic Kernel and not any
> architectural / security design practices to be used.

### Watch the Authenticated API’s Sample Quick Start [Video](https://aka.ms/SK-Samples-AuthAPI-Video)

## Running the sample

1. You will need an [Open AI Key](https://openai.com/api/) or
   [Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart)
   for this sample
2. Ensure the service API is already running `http://localhost:7071`. If not learn
   how to start it [here](../../dotnet/KernelHttpServer/README.md).
3. You will also need to
   [register your application](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app)
   in the Azure Portal. Follow the steps to register your app
   [here](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app).
    - Select **`Single-page application (SPA)`** as platform type, and the Redirect URI will be **`http://localhost:3000`**
    - It is recommended you use the **`Personal Microsoft accounts`** account type for this sample.
4. Once registered, copy the **Application (client) ID** from the Azure Portal and paste
   the GUID into the **[.env](.env)** file next to `REACT_APP_GRAPH_CLIENT_ID=` (first line of the .env file).
5. **Run** the following command `yarn install` (if you have never run the sample before)
   and/or `yarn start` from the command line.
6. A browser will automatically open, otherwise you can navigate to `http://localhost:3000` to use the sample.

## About the Authenticated API’s Sample

The Authenticated API’s sample allows you to use authentication to connect to the
Microsoft Graph using your personal account.

If you don’t have a Microsoft account or do not want to connect to it,
you can review the code to see the patterns needed to call out to APIs.

The sample highlights connecting to Microsoft Graph and calling APIs for Outlook, OneDrive, and ToDo.
Each function will call Microsoft Graph and/or Open AI to perform the tasks.

> [!CAUTION]
> Each function will call Open AI which will use tokens that you will be billed for.
