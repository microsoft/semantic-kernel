---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: dmytrostruk
date: 2023-01-29
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk
---

# Retrieval-Augmented Generation (RAG) in Semantic Kernel

## Context and Problem Statement

### General information

There are several ways how to use RAG pattern in Semantic Kernel (SK). Some of the approaches already exist in SK, and some of them could be added in the future for diverse development experience.

The purpose of this ADR is to describe problematic places with memory-related functionality in SK, demonstrate how to achieve RAG in current version of SK and propose new design of public API for RAG.

Considered options, that are presented in this ADR, do not contradict each other and can be supported all at the same time. The decision which option to support will be based on different factors including priority, actual requirement for specific functionality and general feedback.

### Vector DB integrations - Connectors

There are 12 [vector DB connectors](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Connectors) (also known as `memory connectors`) implemented at the moment, and it may be unclear for developers how to use them. It's possible to call connector methods directly or use it via `TextMemoryPlugin` from [Plugins.Memory](https://www.nuget.org/packages/Microsoft.SemanticKernel.Plugins.Memory) NuGet package (prompt example: `{{recall 'company budget by year'}} What is my budget for 2024?`)

Each connector has unique implementation, some of them rely on already existing .NET SDK from specific vector DB provider, and some of them have implemented functionality to use REST API of vector DB provider.

Ideally, each connector should be always up-to-date and support new functionality. For some connectors maintenance cost is low, since there are no breaking changes included in new features or vector DB provides .NET SDK which is relatively easy to re-use. For other connectors maintenance cost is high, since some of them are still in `alpha` or `beta` development stage, breaking changes can be included or .NET SDK is not provided, which makes it harder to update.

### IMemoryStore interface

Each memory connector implements `IMemoryStore` interface with methods like `CreateCollectionAsync`, `GetNearestMatchesAsync` etc., so it can be used as part of `TextMemoryPlugin`.

By implementing the same interface, each integration is aligned, which makes it possible to use different vector DBs at runtime. At the same time it is disadvantage, because each vector DB can work differently, and it becomes harder to fit all integrations into already existing abstraction. For example, method `CreateCollectionAsync` from `IMemoryStore` is used when application tries to add new record to vector DB to the collection, which doesn't exist, so before insert operation, it creates new collection. In case of [Pinecone](https://www.pinecone.io/) vector DB, this scenario is not supported, because Pinecone index creation is an asynchronous process - API service will return 201 Created HTTP response with following property in response body (index is not ready for usage):

```json
{
    // Other properties...
    "status": {
        "ready": false,
        "state": "Initializing"
    }
}
```

In this case, it's impossible to insert a record to database immediately, so HTTP polling or similar mechanism should be implemented to cover this scenario.

### MemoryRecord as storage schema

`IMemoryStore` interface uses `MemoryRecord` class as storage schema in vector DB. This means that `MemoryRecord` properties should be aligned to all possible connectors. As soon as developers will use this schema in their databases, any changes to schema may break the application, which is not a flexible approach.

`MemoryRecord` contains property `ReadOnlyMemory<float> Embedding` for embeddings and `MemoryRecordMetadata Metadata` for embeddings metadata. `MemoryRecordMetadata` contains properties like:

- `string Id` - unique identifier.
- `string Text` - data-related text.
- `string Description` - optional title describing the content.
- `string AdditionalMetadata` - field for saving custom metadata with a record.

Since `MemoryRecord` and `MemoryRecordMetadata` are not sealed classes, it should be possible to extend them and add more properties as needed. Although, current approach still forces developers to have specific base schema in their vector DBs, which ideally should be avoided. Developers should have the ability to work with any schema of their choice, which will cover their business scenarios (similarly to Code First approach in Entity Framework).

### TextMemoryPlugin

TextMemoryPlugin contains 4 Kernel functions:

- `Retrieve` - returns concrete record from DB by key.
- `Recall` - performs vector search and returns multiple records based on relevance.
- `Save` - saves record in vector DB.
- `Remove` - removes record from vector DB.

All functions can be called directly from prompt. Moreover, as soon as these functions are registered in Kernel and Function Calling is enabled, LLM may decide to call specific function to achieve provided goal.

`Retrieve` and `Recall` functions are useful to provide some context to LLM and ask a question based on data, but functions `Save` and `Remove` perform some manipulations with data in vector DB, which could be unpredicted or sometimes even dangerous (there should be no situations when LLM decides to remove some records, which shouldn't be deleted).

## Decision Drivers

1. All manipulations with data in Semantic Kernel should be safe.
2. There should be a clear way(s) how to use RAG pattern in Semantic Kernel.
3. Abstractions should not block developers from using vector DB of their choice with functionality, that cannot be achieved with provided interfaces or data types.

## Out of scope

Some of the RAG-related frameworks contain functionality to support full cycle of RAG pattern:

1. **Read** data from specific resource (e.g. Wikipedia, OneDrive, local PDF file).
2. **Split** data in multiple chunks using specific logic.
3. **Generate** embeddings from data.
4. **Store** data to preferred vector DB.
5. **Search** data in preferred vector DB based on user query.
6. **Ask** LLM a question based on provided data.

As for now, Semantic Kernel has following experimental features:

- `TextChunker` class to **split** data in chunks.
- `ITextEmbeddingGenerationService` abstraction and implementations to **generate** embeddings using OpenAI and HuggingFace models.
- Memory connectors to **store** and **search** data.

Since these features are experimental, they may be deprecated in the future if the decisions for RAG pattern won't require to provide and maintain listed abstractions, classes and connectors in Semantic Kernel.

Tools for data **reading** is out of scope as for now.

## Considered Options

### Option 1 [Supported] - Prompt concatenation

This option allows to manually construct a prompt with data, so LLM can respond to query based on provided context. It can be achieved by using manual string concatenation or by using prompt template and Kernel arguments. Developers are responsible for integration with vector DB of their choice, data search and prompt construction to send it to LLM.

This approach doesn't include any memory connectors in Semantic Kernel out-of-the-box, but at the same time it gives an opportunity for developers to handle their data in the way that works for them the best.

String concatenation:

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

var builder = new StringBuilder();

// User is responsible for searching the data in a way of their choice, this is an example how it could look like.
var data = await this._vectorDB.SearchAsync("Company budget by year");

builder.AppendLine(data);
builder.AppendLine("What is my budget for 2024?");

var result = await kernel.InvokePromptAsync(builder.ToString());
```

Prompt template and Kernel arguments:

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

// User is responsible for searching the data in a way of their choice, this is an example how it could look like.
var data = await this._vectorDB.SearchAsync("Company budget by year");

var arguments = new KernelArguments { ["budgetByYear"] = data };

var result = await kernel.InvokePromptAsync("{{budgetByYear}} What is my budget for 2024?", arguments);
```

### Option 2 [Supported] - Memory as Plugin

This approach is similar to Option 1, but data search step is part of prompt rendering process. Following list contains possible plugins to use for data search:

- [ChatGPT Retrieval Plugin](https://github.com/openai/chatgpt-retrieval-plugin) - this plugin should be hosted as a separate service. It has integration with various [vector databases](https://github.com/openai/chatgpt-retrieval-plugin?tab=readme-ov-file#choosing-a-vector-database).
- [SemanticKernel.Plugins.Memory.TextMemoryPlugin](https://www.nuget.org/packages/Microsoft.SemanticKernel.Plugins.Memory) - Semantic Kernel solution, which supports various [vector databases](https://learn.microsoft.com/en-us/semantic-kernel/memories/vector-db#available-connectors-to-vector-databases).
- Custom user plugin.

ChatGPT Retrieval Plugin:

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

// Import ChatGPT Retrieval Plugin using OpenAPI specification
// https://github.com/openai/chatgpt-retrieval-plugin/blob/main/.well-known/openapi.yaml
await kernel.ImportPluginFromOpenApiAsync("ChatGPTRetrievalPlugin", openApi!, executionParameters: new(authCallback: async (request, cancellationToken) =>
{
    request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", "chat-gpt-retrieval-plugin-token");
}));

const string Query = "What is my budget for 2024?";
const string Prompt = "{{ChatGPTRetrievalPlugin.query_query_post queries=$queries}} {{$query}}";

var arguments = new KernelArguments
{
    ["query"] = Query,
    ["queries"] = JsonSerializer.Serialize(new List<object> { new { query = Query, top_k = 1 } }),
};

var result = await kernel.InvokePromptAsync(Prompt, arguments);
```

TextMemoryPlugin:

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

// NOTE: If the decision will be to continue support memory-related public API, then it should be revisited.
// It should be up-to-date with new Semantic Kernel patterns.
// Example: instead of `WithChromaMemoryStore`, it should be `AddChromaMemoryStore`.
var memory = new MemoryBuilder()
    .WithChromaMemoryStore("https://chroma-endpoint")
    .WithOpenAITextEmbeddingGeneration("text-embedding-ada-002", "api-key")
    .Build();

kernel.ImportPluginFromObject(new TextMemoryPlugin(memory));

var result = await kernel.InvokePromptAsync("{{recall 'Company budget by year'}} What is my budget for 2024?");
```

Custom user plugin:

```csharp
public class MyDataPlugin
{
    [KernelFunction("search")]
    public async Task<string> SearchAsync(string query)
    {
        // Make a call to vector DB and return results.
        // Here developer can use already existing .NET SDK from specific vector DB provider.
        // It's also possible to re-use Semantic Kernel memory connector directly here: 
        // new ChromaMemoryStore(...).GetNearestMatchAsync(...)
    }
}

var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

kernel.ImportPluginFromType<MyDataPlugin>();

var result = await kernel.InvokePromptAsync("{{search 'Company budget by year'}} What is my budget for 2024?");
```

The reason why custom user plugin is more flexible than `TextMemoryPlugin` is because `TextMemoryPlugin` requires all vector DBs to implement `IMemoryStore` interface with disadvantages described above, while custom user plugin can be implemented in a way of developer's choice. There won't be any restrictions on DB record schema or requirement to implement specific interface.

### Option 3 [Partially supported] - Prompt concatenation using Prompt Filter

This option is similar to Option 1, but prompt concatenation will happen on Prompt Filter level:

Prompt filter:

```csharp
public sealed class MyPromptFilter : IPromptFilter
{
    public void OnPromptRendering(PromptRenderingContext context)
    {
        // Handling of prompt rendering event...
    }

    public void OnPromptRendered(PromptRenderedContext context)
    {
        var data = "some data";
        var builder = new StringBuilder();

        builder.AppendLine(data);
        builder.AppendLine(context.RenderedPrompt);

        // Override rendered prompt before sending it to AI and include data
        context.RenderedPrompt = builder.ToString();
    }
}
```

Usage:

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

kernel.PromptFilters.Add(new MyPromptFilter());

var result = await kernel.InvokePromptAsync("What is my budget for 2024?");
```

From the usage perspective, prompt will contain just user query without additional data. The data will be added to the prompt behind the scenes.

The reason why this approach is **partially supported** is because a call to vector DB most probably will be an asynchronous, but current Kernel filters don't support asynchronous scenarios. So, in order to support asynchronous calls, new type of filters should be added to Kernel: `IAsyncFunctionFilter` and `IAsyncPromptFilter`. They will be the same as current `IFunctionFilter` and `IPromptFilter` but with async methods.

### Option 4 [Proposal] - Memory as part of PromptExecutionSettings

This proposal is another possible way how to implement RAG pattern in SK, on top of already existing approaches described above. Similarly to `TextMemoryPlugin`, this approach will require abstraction layer and each vector DB integration will be required to implement specific interface (it could be existing `IMemoryStore` or completely new one) to be compatible with SK. As described in _Context and Problem Statement_ section, the abstraction layer has its advantages and disadvantages.

User code will look like this:

```csharp
var kernel = Kernel.CreateBuilder()
    .AddOpenAIChatCompletion("model-id", "api-key")
    .Build();

var executionSettings = new OpenAIPromptExecutionSettings
{
    Temperature = 0.8,
    MemoryConfig = new()
    {
        // This service could be also registered using DI with specific lifetime
        Memory = new ChromaMemoryStore("https://chroma-endpoint"),
        MinRelevanceScore = 0.8,
        Limit = 3
    }
};

var function = KernelFunctionFactory.CreateFromPrompt("What is my budget for 2024?", executionSettings);

var result = await kernel.InvokePromptAsync("What is my budget for 2024?");
```

Data search and prompt concatenation will happen behind the scenes in `KernelFunctionFromPrompt` class.

## Decision Outcome

Temporary decision is to provide more examples how to use memory in Semantic Kernel as Plugin.

The final decision will be ready based on next memory-related requirements.
