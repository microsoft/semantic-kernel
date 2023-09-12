# Semantic Kernel syntax examples

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
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
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

# Azure Cognitive Search
ACS__Endpoint
ACS__ApiKey

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
