# OpenAI Connector Migration Guide

This manual prepares you for the migration of your OpenAI Connector to the new OpenAI Connector. The new OpenAI Connector is a complete rewrite of the existing OpenAI Connector and is designed to be more efficient, reliable, and scalable. This manual will guide you through the migration process and help you understand the changes that have been made to the OpenAI Connector.

## 1. Package Setup when Using Azure

If you are working with Azure and or OpenAI public APIs, you will need to change the package from `Microsoft.SemanticKernel.Connectors.OpenAI` to `Microsoft.SemanticKernel.Connectors.AzureOpenAI`,

> [!IMPORTANT]
> The `Microsoft.SemanticKernel.Connectors.AzureOpenAI` package depends on the `Microsoft.SemanticKernel.Connectors.OpenAI` package so there's no need to add both to your project when using `OpenAI` related types.

```diff
- // Before
- using Microsoft.SemanticKernel.Connectors.OpenAI;
+ After
+ using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
```

### 1.1 AzureOpenAIClient

When using Azure with OpenAI, before where you were using `OpenAIClient` you will need to update your code to use the new `AzureOpenAIClient` type.

### 1.2 Services

All services below now belong to the `Microsoft.SemanticKernel.Connectors.AzureOpenAI` namespace.

- `AzureOpenAIAudioToTextService`
- `AzureOpenAIChatCompletionService`
- `AzureOpenAITextEmbeddingGenerationService`
- `AzureOpenAITextToAudioService`
- `AzureOpenAITextToImageService`

## 2. Text Generation Deprecated

The latest `OpenAI` SDK does not support text generation modality, when migrating to their underlying SDK we had to drop the support and removed `TextGeneration` specific services but the existing `ChatCompletion` ones still supports (implements `ITextGenerationService`).

If you were using any of the `OpenAITextGenerationService` or `AzureOpenAITextGenerationService` you will need to update your code to target a chat completion model instead, using `OpenAIChatCompletionService` or `AzureOpenAIChatCompletionService` instead.

> [!NOTE]
> OpenAI and AzureOpenAI `ChatCompletion` services also implement the `ITextGenerationService` interface and that may not require any changes to your code if you were targeting the `ITextGenerationService` interface.

tags:
`OpenAITextGenerationService`,`AzureOpenAITextGenerationService`,
`AddOpenAITextGeneration`,`AddAzureOpenAITextGeneration`

## 3. ChatCompletion Multiple Choices Deprecated

The latest `OpenAI` SDK does not support multiple choices, when migrating to their underlying SDK we had to drop the support and removed `ResultsPerPrompt` also from the `OpenAIPromptExecutionSettings`.

tags: `ResultsPerPrompt`,`results_per_prompt`

## 4. OpenAI File Service Deprecation

The `OpenAIFileService` was deprecated in the latest version of the OpenAI Connector. We strongly recommend to update your code to use the new `OpenAIClient.GetFileClient()` for file management operations.

## 5. OpenAI ChatCompletion custom endpoint

The `OpenAIChatCompletionService` **experimental** constructor for custom endpoints will not attempt to auto-correct the endpoint and use it as is.

We have the two only specific cases where we attempted to auto-correct the endpoint.

1. If you provided `chat/completions` path before. Now those need to be removed as they are added automatically to the end of your original endpoint by `OpenAI SDK`.

   ```diff
   - http://any-host-and-port/v1/chat/completions
   + http://any-host-and-port/v1
   ```

2. If you provided a custom endpoint without any path. We won't be adding the `v1/` as the first path. Now the `v1` path needs to provided as part of your endpoint.

   ```diff
   - http://any-host-and-port/
   + http://any-host-and-port/v1
   ```

## 6. SemanticKernel MetaPackage

To be retro compatible with the new OpenAI and AzureOpenAI Connectors, our `Microsoft.SemanticKernel` meta package changed its dependency to use the new `Microsoft.SemanticKernel.Connectors.AzureOpenAI` package that depends on the `Microsoft.SemanticKernel.Connectors.OpenAI` package. This way if you are using the metapackage, no change is needed to get access to `Azure` related types.

## 7. Contents

### 7.1 OpenAIChatMessageContent

- The `Tools` property type has changed from `IReadOnlyList<ChatCompletionsToolCall>` to `IReadOnlyList<ChatToolCall>`.

- Inner content type has changed from `ChatCompletionsFunctionToolCall` to `ChatToolCall`.

- Metadata type `FunctionToolCalls` has changed from `IEnumerable<ChatCompletionsFunctionToolCall>` to `IEnumerable<ChatToolCall>`.

### 7.2 OpenAIStreamingChatMessageContent

- The `FinishReason` property type has changed from `CompletionsFinishReason` to `FinishReason`.
- The `ToolCallUpdate` property has been renamed to `ToolCallUpdates` and its type has changed from `StreamingToolCallUpdate?` to `IReadOnlyList<StreamingToolCallUpdate>?`.
- The `AuthorName` property is not initialized because it's not provided by the underlying library anymore.

## 7.3 Metrics for AzureOpenAI Connector

The meter `s_meter = new("Microsoft.SemanticKernel.Connectors.OpenAI");` and the relevant counters still have old names that contain "openai" in them, such as:

- `semantic_kernel.connectors.openai.tokens.prompt`
- `semantic_kernel.connectors.openai.tokens.completion`
- `semantic_kernel.connectors.openai.tokens.total`

## 8. Using Azure with your data (Data Sources)

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
var promptExecutionSettings = new AzureOpenAIPromptExecutionSettings
{
    AzureChatDataSource = new AzureSearchChatDataSource
    {
         Endpoint = new Uri(TestConfiguration.AzureAISearch.Endpoint),
         Authentication = DataSourceAuthentication.FromApiKey(TestConfiguration.AzureAISearch.ApiKey),
         IndexName = TestConfiguration.AzureAISearch.IndexName
    }
};
```

## 9. Breaking glass scenarios

Breaking glass scenarios are scenarios where you may need to update your code to use the new OpenAI Connector. Below are some of the breaking changes that you may need to be aware of.

#### 9.1 KernelContent Metadata

Some of the keys in the content metadata dictionary have changed, you will need to update your code to when using the previous key names.

- `Created` -> `CreatedAt`

#### 9.2 Prompt Filter Results

The `PromptFilterResults` metadata type has changed from `IReadOnlyList<ContentFilterResultsForPrompt>` to `ContentFilterResultForPrompt`.

#### 9.3 Content Filter Results

The `ContentFilterResultsForPrompt` type has changed from `ContentFilterResultsForChoice` to `ContentFilterResultForResponse`.

#### 9.4 Finish Reason

The FinishReason metadata string value has changed from `stop` to `Stop`

#### 9.5 Tool Calls

The ToolCalls metadata string value has changed from `tool_calls` to `ToolCalls`

#### 9.6 LogProbs / Log Probability Info

The `LogProbabilityInfo` type has changed from `ChatChoiceLogProbabilityInfo` to `IReadOnlyList<ChatTokenLogProbabilityInfo>`.

#### 9.7 Finish Details, Index, and Enhancements

All of above have been removed.

#### 9.8 Token Usage

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

#### 9.9 OpenAIClient

The `OpenAIClient` type previously was a Azure specific namespace type but now it is an `OpenAI` SDK namespace type, you will need to update your code to use the new `OpenAIClient` type.

When using Azure, you will need to update your code to use the new `AzureOpenAIClient` type.

#### 9.10 Pipeline Configuration

The new `OpenAI` SDK uses a different pipeline configuration, and has a dependency on `System.ClientModel` package. You will need to update your code to use the new `HttpClientPipelineTransport` transport configuration where before you were using `HttpClientTransport` from `Azure.Core.Pipeline`.

[Example of Pipeline Configuration](https://github.com/microsoft/semantic-kernel/pull/7151/files#diff-fab02d9a75bf43cb57f71dddc920c3f72882acf83fb125d8cad963a643d26eb3)

```diff
var clientOptions = new OpenAIClientOptions
{
-    // Before: From Azure.Core.Pipeline
-    Transport = new HttpClientTransport(httpClient),

+    // After: From OpenAI SDK -> System.ClientModel
+    Transport = new HttpClientPipelineTransport(httpClient),
};
```
