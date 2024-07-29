# BugBash Guidance

- Get the Bugbash branch `features/bugbash-prep` from `microsoft/semantic-kernel`
- Open the Solution in Visual Studio
- Go to `samples`, `Before` and try to build each project individually.

  Each project may have different impacts on preparing it to be compatible with OpenAI V2 connector.

  All required changes are what the customers will have to do to migrate their code to the new OpenAI Connector.

## Goals:

### 1. Low code changes required to make the code compatible

### 2. (Before) Projects build successfully

### 3. (Before) Tests run and pass successfully

### 4. Identify any lacking information or guidance provided below towards the migration.

## Troubleshooting

If you are having trouble migrating, check the (After) folders on how that was done. Sometimes some thats had to be dropped/changed completely like: `Multiple Choices` and `Text Generation` for example.

# OpenAI Connector Migration Guide

This manual prepares you for the migration of your OpenAI Connector to the new OpenAI Connector. The new OpenAI Connector is a complete rewrite of the existing OpenAI Connector and is designed to be more efficient, reliable, and scalable. This manual will guide you through the migration process and help you understand the changes that have been made to the OpenAI Connector.

## Package Setup when Using Azure

If you are working with Azure and or OpenAI public APIs, you will need to change the package from `Microsoft.SemanticKernel.Connectors.OpenAI` to `Microsoft.SemanticKernel.Connectors.AzureOpenAI`,

> Note: The `Microsoft.SemanticKernel.Connectors.AzureOpenAI` package depends on the `Microsoft.SemanticKernel.Connectors.OpenAI` package so there's no need to add both to your project when using `OpenAI` related types.

Before

```csharp
using Microsoft.SemanticKernel.Connectors.OpenAI;
```

After

```csharp
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
```

## Breaking Glass scenarios

### Metadata

#### Token Usage

The Token usage naming convention from `OpenAI` changed from `Completion`, `Prompt` tokens to `Output` and `Input` respectively. You will need to update your code to use the new naming.

The type also changed from `CompletionsUsage` to `ChatTokenUsage`.

[Example of Token Usage Metadata Changes](https://github.com/microsoft/semantic-kernel/pull/7151/files#diff-a323107b9f8dc8559a83e50080c6e34551ddf6d9d770197a473f249589e8fb47)

```diff
- Before
- var usage = FunctionResult.Metadata?["Usage"] as CompletionsUsage;
- var completionTokesn = usage?.CompletionTokens ?? 0;
- var promptTokens = usage?.PromptTokens ?? 0;

+ After
+ var usage = FunctionResult.Metadata?["Usage"] as ChatTokenUsage;
+ var promptTokens = usage?.InputTokens ?? 0;
+ var completionTokens = completionTokens: usage?.OutputTokens ?? 0;

totalTokens: usage?.TotalTokens ?? 0;
```

### OpenAIClient

The `OpenAIClient` type previously was a Azure specific namespace type but now it is an `OpenAI` SDK namespace type, you will need to update your code to use the new `OpenAIClient` type.

When using Azure, you will need to update your code to use the new `AzureOpenAIClient` type.

#### Pipeline Configuration

[Example of Pipeline Configuration](https://github.com/microsoft/semantic-kernel/pull/7151/files#diff-fab02d9a75bf43cb57f71dddc920c3f72882acf83fb125d8cad963a643d26eb3)

```diff
var clientOptions = new OpenAIClientOptions
{
-    // Before: From Azure.Core.Pipeline
-    Transport = new HttpClientTransport(httpClient),

+    // After: From OpenAI SDK
+    Transport = new HttpClientPipelineTransport(httpClient),
};
```

## Text Generation Deprecated

The `TextGeneration` modality was deprecated in the latest version of the OpenAI Connector. You will need to update your code to use `ChatCompletion` modality instead. Keep in mind that the `ChatCompletion` services also implement the `TextGeneration` interface and that may not require any changes to your code if you were targetting the `ITextGenerationService` interface.

## ChatCompletion Multiple Choices Deprecated

The lastest `OpenAI` SDK does not support multiple choices anymore. The option for multiple results was removed also from the `OpenAIPromptExecutionSettings`. So any implementation that was relying on multiple choices will need to be updated.

## Using Azure with your data (Data Sources)

With the new `AzureOpenAIClient`, you can now specify your datasource thru the options and that requires a small change in your code to the new type.

Before

```csharp
var promptExecutionSettings = new OpenAIPromptExecutionSettings
{
    AzureChatExtensionsOptions = new AzureChatExtensionsOptions
    {
        Extensions = [ new AzureSearchChatExtensionConfiguration
        {
            SearchEndpoint = new Uri(TestConfiguration.AzureAISearch.Endpoint),
            Authentication = new OnYourDataApiKeyAuthenticationOptions(TestConfiguration.AzureAISearch.ApiKey),
            IndexName = TestConfiguration.AzureAISearch.IndexName
        }]
    };
};
```

After

```csharp
var promptExecutionSettings = new AzureOpenAIPromptExecutionSettings {
    AzureChatDataSource = new AzureSearchChatDataSource
    {
         Endpoint = new Uri(TestConfiguration.AzureAISearch.Endpoint),
         Authentication = DataSourceAuthentication.FromApiKey(TestConfiguration.AzureAISearch.ApiKey),
         IndexName = TestConfiguration.AzureAISearch.IndexName
    }
};

```

## OpenAI File Service Deprecation

The `OpenAIFileService` was deprecated in the latest version of the OpenAI Connector. We strongly recommend to update your code to use the new `OpenAIClient.GetFileClient()` for file management operations.

## SemanticKernel MetaPackage

To be retro compatible with the new OpenAI and AzureOpenAI Connectors, our `Microsoft.SemanticKernel` meta package changed its dependency to use the new `Microsoft.SemanticKernel.Connectors.AzureOpenAI` package that depends on the `Microsoft.SemanticKernel.Connectors.OpenAI` package. This way if you are using the metapackage, no change is needed to get access to `Azure` related types.
