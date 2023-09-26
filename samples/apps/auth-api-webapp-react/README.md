# Authenticated API’s Sample Learning App

> [!IMPORTANT]
> This sample will be removed in a future release. If you are looking for samples that demonstrate
> how to use Semantic Kernel, please refer to the sample folders in the root [python](../../../python/samples/)
> and [dotnet](../../../dotnet/samples/) folders.

> [!IMPORTANT]
> This learning sample is for educational purposes only and should not be used in any production
> use case. It is intended to highlight concepts of Semantic Kernel and not any
> architectural / security design practices to be used.

### Watch the Authenticated API’s Sample Quick Start [Video](https://aka.ms/SK-Samples-AuthAPI-Video)

## Running the sample

1. You will need an [Open AI Key](https://openai.com/api/) or
   [Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart)
   for this sample
2. Ensure the KernelHttpServer sample is already running at `http://localhost:7071`. If not, follow the steps
   to start it [here](../../dotnet/KernelHttpServer/README.md).
3. You will also need to
   [register your application](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app)
   in the Azure Portal. Follow the steps to register your app
   [here](https://learn.microsoft.com/azure/active-directory/develop/quickstart-register-app).
    - Select **`Single-page application (SPA)`** as platform type, and the Redirect URI will be **`http://localhost:3000`**
    - Select **`Personal Microsoft accounts only`** as supported account types for this sample
4. Copy **[.env.example](.env.example)** into a new file with name "**.env**".
    > **Note**: Samples are configured to use chat completion AI models (e.g., gpt-3.5-turbo, gpt-4, etc.). See https://platform.openai.com/docs/models/model-endpoint-compatibility for chat completion model options.
5. Once registered, copy the **Application (client) ID** from the Azure Portal and paste
   the GUID into the **.env** file next to `REACT_APP_GRAPH_CLIENT_ID=` (first line of the .env file).
6. **Run** the following command `yarn install` (if you have never run the sample before)
   and/or `yarn start` from the command line.
7. A browser will automatically open, otherwise you can navigate to `http://localhost:3000` to use the sample.

> Working with Secrets: [KernelHttpServer's Readme](../../dotnet/KernelHttpServer/README.md#Working-with-Secrets) has a note on safely working with keys and other secrets.

## About the Authenticated API’s Sample

The Authenticated API’s sample allows you to use authentication to connect to the
Microsoft Graph using your personal account.

If you don’t have a Microsoft account or do not want to connect to it,
you can review the code to see the patterns needed to call out to APIs.

The sample highlights connecting to Microsoft Graph and calling APIs for Outlook, OneDrive, and ToDo.
Each function will call Microsoft Graph and/or Open AI to perform the tasks.

> [!CAUTION]
> Each function will call Open AI which will use tokens that you will be billed for.

## Troubleshooting

### unauthorized_client: The client does not exist or is not enabled for consumers.

1. Ensure in your Application Manifest that **`Personal Microsoft accounts`** are allowed to sign in.

    - `"signInAudience": "PersonalMicrosoftAccount"` or
    - `"signInAudience": "AzureADandPersonalMicrosoftAccount"`

2. If you are not able to change the manifest, create a new Application following the instructions in [Running the sample](#running-the-sample), step 3.
