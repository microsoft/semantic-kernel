#Semantic Kernel syntax examples

This project contains a collection of semi-random examples about various scenarios
using SK components.

The examples are ordered by number, starting with very basic examples.

## Running Examples with Filters

You can run individual examples in the KernelSyntaxExamples project using various methods to specify a filter. This allows you to execute specific examples without running all of them. Choose one of the following options to apply a filter:

### Option 1: Set the Default Filter in Program.cs

In your code, you can set a default filter by modifying the appropriate variable or parameter. Look for the section in your code where the filter is applied or where the examples are defined, and change the filter value accordingly.

```csharp
// Example of setting a default filter in code
string defaultFilter = "Example0"; // will run all examples that contain 'example0' in the name
```

### Option 2: Set Command-Line Arguments

Right-click on your console application project in the Solution Explorer.

Choose "Properties" from the context menu.

In the project properties window, navigate to the "Debug" tab on the left.

Supply Command-Line Arguments:

In the "Command line arguments" field, enter the command-line arguments that your console application expects. Separate multiple arguments with spaces.

### Option 3: Use Visual Studio Code Filters

If you are using Visual Studio Code, you can specify a filter using the built-in filter options provided by the IDE. These options can be helpful when running your code in a debugging environment. Consult the documentation for Visual Studio Code or the specific extension you're using for information on applying filters.

### Option 4: Modify launch.json

If you are using Visual Studio or a similar IDE that utilizes launch configurations, you can specify the filter in your launch.json configuration file. Edit the configuration for your project to include the filter parameter.

## Configuring Secrets

Most of the examples will require secrets and credentials, to access OpenAI, Azure OpenAI,
Bing and other resources. We suggest using .NET
[Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets)
to avoid the risk of leaking secrets into the repository, branches and pull requests.
You can also use environment variables if you prefer.

To set your secrets with Secret Manager:

```
cd dotnet/samples/KernelSyntaxExamples

dotnet user-secrets init

dotnet user-secrets set "OpenAI:ModelId" "..."
dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:EmbeddingModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAI:ServiceId" "..."
dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:ModelId" "..."
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:ChatModelId" "..."
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."

dotnet user-secrets set "AzureOpenAIEmbeddings:DeploymentName" "..."
dotnet user-secrets set "AzureOpenAIEmbeddings:Endpoint" "https://... .openai.azure.com/"
dotnet user-secrets set "AzureOpenAIEmbeddings:ApiKey" "..."

dotnet user-secrets set "ACS:Endpoint" "https://... .search.windows.net"
dotnet user-secrets set "ACS:ApiKey" "..."

dotnet user-secrets set "Qdrant:Endpoint" "..."
dotnet user-secrets set "Qdrant:Port" "..."

dotnet user-secrets set "Weaviate:Scheme" "..."
dotnet user-secrets set "Weaviate:Endpoint" "..."
dotnet user-secrets set "Weaviate:Port" "..."
dotnet user-secrets set "Weaviate:ApiKey" "..."

dotnet user-secrets set "KeyVault:Endpoint" "..."
dotnet user-secrets set "KeyVault:ClientId" "..."
dotnet user-secrets set "KeyVault:TenantId" "..."

dotnet user-secrets set "HuggingFace:ApiKey" "..."
dotnet user-secrets set "HuggingFace:ModelId" "..."

dotnet user-secrets set "Pinecone:ApiKey" "..."
dotnet user-secrets set "Pinecone:Environment" "..."

dotnet user-secrets set "Jira:ApiKey" "..."
dotnet user-secrets set "Jira:Email" "..."
dotnet user-secrets set "Jira:Domain" "..."

dotnet user-secrets set "Bing:ApiKey" "..."

dotnet user-secrets set "Google:ApiKey" "..."
dotnet user-secrets set "Google:SearchEngineId" "..."

dotnet user-secrets set "Github:PAT" "github_pat_..."

dotnet user-secrets set "Apim:Endpoint" "https://apim...azure-api.net/"
dotnet user-secrets set "Apim:SubscriptionKey" "..."

dotnet user-secrets set "Postgres:ConnectionString" "..."
dotnet user-secrets set "Redis:Configuration" "..."
dotnet user-secrets set "Kusto:ConnectionString" "..."
```

To set your secrets with environment variables, use these names:

```
# OpenAI
OpenAI__ModelId
OpenAI__ChatModelId
OpenAI__EmbeddingModelId
OpenAI__ApiKey

# Azure OpenAI
AzureOpenAI__ServiceId
AzureOpenAI__DeploymentName
AzureOpenAI__ChatDeploymentName
AzureOpenAI__Endpoint
AzureOpenAI__ApiKey

AzureOpenAIEmbeddings__DeploymentName
AzureOpenAIEmbeddings__Endpoint
AzureOpenAIEmbeddings__ApiKey

# Azure AI Search
AzureAISearch__Endpoint
AzureAISearch__ApiKey

# Qdrant
Qdrant__Endpoint
Qdrant__Port

# Weaviate
Weaviate__Scheme
Weaviate__Endpoint
Weaviate__Port
Weaviate__ApiKey

# Azure Key Vault
KeyVault__Endpoint
KeyVault__ClientId
KeyVault__TenantId

# Hugging Face
HuggingFace__ApiKey
HuggingFace__ModelId

# Pinecone
Pinecone__ApiKey
Pinecone__Environment

# Jira
Jira__ApiKey
Jira__Email
Jira__Domain

# Bing
Bing__ApiKey

# Google
Google__ApiKey
Google__SearchEngineId

# Github
Github__PAT

# Azure API Management (APIM)
Apim__Endpoint
Apim__SubscriptionKey

# Other
Postgres__ConnectionString
Redis__Configuration
```

# Authentication for the OpenAPI Functions

The Semantic Kernel OpenAPI Function enables developers to take any REST API that follows the OpenAPI specification and import it as a plugin to the Semantic Kernel. However, the Kernel needs to be able to authenticate outgoing requests per the requirements of the target API. This document outlines the authentication model for the OpenAPI plugin.

## The `AuthenticateRequestAsyncCallback` delegate

`AuthenticateRequestAsyncCallback` is a delegate type that serves as a callback function for adding authentication information to HTTP requests sent by the OpenAPI plugin.

```csharp
public delegate Task AuthenticateRequestAsyncCallback(HttpRequestMessage request);
```

Developers may optionally provide an implementation of this delegate when importing an OpenAPI plugin to the Kernel. The delegate is then passed through to the `RestApiOperationRunner`, which is responsible for building the HTTP payload and sending the request for each REST API operation. Before the API request is sent, the delegate is executed with the HTTP request message as the parameter, allowing the request message to be updated with any necessary authentication information.

This pattern was designed to be flexible enough to support a wide variety of authentication frameworks.

## Authentication Providers example

### BasicAuthenticationProvider

This class implements the HTTP "basic" authentication scheme. The constructor accepts a `Func` which defines how to retrieve the user's credentials. When the `AuthenticateRequestAsync` method is called, it retrieves the credentials, encodes them as a UTF-8 encoded Base64 string, and adds them to the `HttpRequestMessage`'s authorization header.

The following code demonstrates how to use this provider:

```csharp
var basicAuthProvider = new BasicAuthenticationProvider(() =>
{
    // JIRA API expects credentials in the format "email:apikey"
    return Task.FromResult(
        Env.Var("MY_EMAIL_ADDRESS") + ":" + Env.Var("JIRA_API_KEY")
    );
});
var plugin = kernel.ImportOpenApiPluginFromResource(PluginResourceNames.Jira, new OpenApiFunctionExecutionParameters { AuthCallback = basicAuthProvider.AuthenticateRequestAsync } );
```

### BearerAuthenticationProvider

This class implements the HTTP "bearer" authentication scheme. The constructor accepts a `Func` which defines how to retrieve the bearer token. When the `AuthenticateRequestAsync` method is called, it retrieves the token and adds it to the `HttpRequestMessage`'s authorization header.

The following code demonstrates how to use this provider:

```csharp
var bearerAuthProvider = new BearerAuthenticationProvider(() =>
{
    return Task.FromResult(Env.Var("AZURE_KEYVAULT_TOKEN"));
});
var plugin = kernel.ImportOpenApiPluginFromResource(PluginResourceNames.AzureKeyVault, new OpenApiFunctionExecutionParameters { AuthCallback =  bearerAuthProvider.AuthenticateRequestAsync } )
```

### InteractiveMsalAuthenticationProvider

This class uses the [Microsoft Authentication Library (MSAL)](https://learn.microsoft.com/en-us/azure/active-directory/develop/msal-overview)'s .NET library to authenticate the user and acquire an OAuth token. It follows the interactive [authorization code flow](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow), requiring the user to sign in with a Microsoft or Azure identity. This is particularly useful for authenticating requests to the Microsoft Graph or Azure APIs.

Once the token is acquired, it is added to the HTTP authentication header via the `AuthenticateRequestAsync` method, which is inherited from `BearerAuthenticationProvider`.

To construct this provider, the caller must specify:

- _Client ID_ – identifier of the calling application. This is acquired by [registering your application with the Microsoft Identity platform](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).
- _Tenant ID_ – identifier of the target service tenant, or “common”
- _Scopes_ – permissions being requested
- _Redirect URI_ – for redirecting the user back to the application. (When running locally, this is typically http://localhost.)

```csharp
var msalAuthProvider = new InteractiveMsalAuthenticationProvider(
    Env.Var("AZURE_KEYVAULT_CLIENTID"), // clientId
    Env.Var("AZURE_KEYVAULT_TENANTID"), // tenantId
    new string[] { ".default" },        // scopes
    new Uri("http://localhost")         // redirectUri
);
var plugin = kernel.ImportOpenApiPluginFromResource(PluginResourceNames.AzureKeyVault, new OpenApiFunctionExecutionParameters { AuthCallback =  msalAuthProvider.AuthenticateRequestAsync } )
```
