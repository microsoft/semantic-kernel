---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: rogerbarreto
date: { YYYY-MM-DD when the decision was last updated }
deciders: markwallace, sergey, dmytro, weslie, evan, shawn
---

# Structured Concepts

## Context and Problem Statement

Currently the Concepts project has is divided per folder where the examples don't follow a same approach and pattern. Method names aren't descriptive, some class have many examples making it harder to find and debug it.

## Decision Drivers

- Samples should be easier to find
- Safe for copy and paste into a console application.
- Fully documented explaining every aspect of what is happening with the code.
- Structured, for docs (readme or ipynb) and source generation

## Problem

A caching example like [Caching/SemanticCachingWithFilters.cs](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Caching/SemanticCachingWithFilters.cs) touches a lot of different concepts like: `Cache`, `Connectors`, `Embeddings`, `Filters`, `Function Invocation Filters`, `Prompt Render Filter`, `Vector Store`, `Vector Store Record`, `Kernel`, `Azure OpenAI`, `OpenAI`, `Dependency Injection`, `Chat Completion`, `Prompt Template`, `Basic Semantic Kernel Template`

Currently this is not an isolated scenario but actually apply for all our samples where in one simple example it can reference a mix of different concepts that makes it very difficult to organize in a definitive folder/file structure.

If we were to find the definitive solution, it would be need to consider all potential permutations which would make it impractical to maintain.

## Solution

We can apply a set of guidelines to the Concepts project to make it easier to find, understand and use the examples. This will also make it easier to generate documentation and source code from the examples in the future. Those guidelines also will help to implement new and existing examples in a consistent way.

### 1. Decorate concepts test classes

Using Concept Attributes on our classes, allowing indexing of samples by multiple concept tags. This also adds the benefit of being specific, compilable and less prone for mistaking add or using a non-existing concept.

Note: Can be easily setup using a proper AI prompt.

```csharp
[UsedConcepts(
    Concepts.Kernel,
    Concepts.FunctionCalling,
    Concepts.AutoFunctionChoiceBehavior,
    ...)]
public class AzureAIInference_FunctionCalling : BaseTest
```

### 2. Each test class MUST have a xmldoc description

There are plenty of test demos in Concepts that lack a better detail and explanation of what is the purpose of the sample, this is very helpful for documentation and user orientation.

Note: Can be easily setup using a proper AI prompt.

✅ Good

```csharp
/// <summary>
/// An example showing how use the VectorStore abstractions to consume data from a Qdrant data store,
/// that was created using the MemoryStore abstractions.
/// </summary>
/// <remarks>
/// The IMemoryStore abstraction has limitations that constrain its use in many scenarios
/// e.g. it only supports a single fixed schema and does not allow search filtering.
/// To provide more flexibility, the Vector Store abstraction has been introduced.
///
/// To run this sample, you need a local instance of Docker running, since the associated fixture
/// will try and start a Qdrant container in the local docker instance to run against.
/// </remarks>
public class VectorStore_ConsumeFromMemoryStore_Qdrant(ITestOutputHelper output, VectorStoreQdrantContainerFixture qdrantFixture) : BaseTest(output), IClassFixture<VectorStoreQdrantContainerFixture>
{
```

❌ Missing detail and is not a XmlDoc

```csharp
// The following example shows how to use Semantic Kernel with Ollama API.
public class Ollama_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
```

### 3. Each fact in the concepts MUST have a descriptive name

Fact method names, MUST provide a clear understanding of what is happening in the test.

| Bad ❌                                     | Good ✅                                                         |
| ------------------------------------------ | --------------------------------------------------------------- |
| `OpenAI_ChatCompletion.ServicePromptAsync` | `OpenAI_ChatCompletion.UsingChatServiceWithStringPromptAsync`   |
| `OpenAI_ChatCompletion.ChatPromptAsync`    | `OpenAI_ChatCompletion.UsingKernelChatPromptSyntaxAsync`        |
| `OpenAI_CustomClient.RunAsync`             | `OpenAI_CustomHttpClient.AddingHeaderWithCustomHttpClientAsync` |

### 4. Each fact in the concepts MUST have xmldoc description

Similar to the class description, each fact should have a description of what is the purpose of the fact, this is very helpful for documentation and user orientation.

This will be very helpful for later Roslyn scrap when needed (ipynb) generation or other dynamic UI indexing.

Note: Can be easily setup using a proper AI prompt with file context.

### 5. Keep the code commented.

The code should be commented in a way that it is easy to understand what is happening in the code. This is very helpful for documentation and user orientation.
This way during the UI rendering each line of comments can be extracted into different code blocks sections automatically.

Note: Can be easily setup using a proper AI prompt with file context.

### 6. Test File Name and Size

The overall rule is to have try to keep as less as possible examples in a single file, splitting the files per group of examples whenever possible.

Normally samples with single file names tends to have multiple examples in the same file, this is not a good practice as it makes it harder to search as well as added cognitive load to understand the file.

File names:

1. Should have at least two words, separated by an underscore, where the first word is the concept or provider and the second is the example name or a group of examples that match the same approach.

2. When the file has examples for a specific `<provider>` it should start with the `<provider>` as the first word. By `<provider>` here also can reflect runtimes, platforms, protocals or services.

Note: Can be easily fixed using a proper AI prompt with file context.

✅ Number of samples: 2

✅ File name: ChatCompletion/Onnx_ChatCompletion.cs - Two words (`<provider>` + Group of tests)

```csharp
public class Onnx_ChatCompletion(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task UsingChatServiceWithStringPromptAsync()
    {
    }

    [Fact]
    public async Task UsingKernelChatPromptSyntaxAsync()
    {
    }
}
```

❌ Number of samples: 3+

❌ File name: FunctionCalling/FunctionCalling.cs - Single name

```csharp
public class FunctionCalling(ITestOutputHelper output) : BaseTest(output)

    [Fact]
    public async Task RunPromptWithAutoFunctionChoiceBehaviorAdvertisingAllKernelFunctionsInvokedAutomaticallyAsync()

    [Fact]
    public async Task RunPromptWithRequiredFunctionChoiceBehaviorAdvertisingOneFunctionInvokedAutomaticallyAsync()

    [Fact]
    public async Task RunPromptWithNoneFunctionChoiceBehaviorAdvertisingAllKernelFunctionsAsync()

    /// Many more
```

✅ Number of samples: 1

❌ File name: Memory/VectorStore_ConsumeFromMemoryStore_Qdrant.cs - Three words ✅, `<provider>` is the last ❌

```csharp
/// <summary> .. detailed description .. </summary>
public class VectorStore_ConsumeFromMemoryStore_Qdrant
{
    [Fact]
    public async Task ConsumeExampleAsync()
}
```

### 7. Simplify folder structure

This is not a mandatory requirement for indexing but would simplify the overall structure of the project.

Common and broader concepts, like `Memory`, `Vector Store`, `Caching`, `Optimization`, `Function Calling`, `Functions`, `Kernel`, `Planners`, `Optimization`, `Prompt Templates`, `Dependency Injection`, `RAG`, `Local Models`, don't need to live in a separate folder structure, but rather can cross cut the folders and examples, with proper tagging they can be easily found thru GUI search or in the proposed Web App.

Proposed simplified folders:

- VectorData
- Chat
- Text (Combining TextTo*Any*)
- Embedding
- Audio (Combining AudioTo*Any*)
- Image (Combining ImageTo*Any*)
- Agents
- Filters
- Plugins
- Process
- Search

Sorting orfans approach:

- `PromptTemplate/ChatCompletionPrompts.cs` -> `Chat/PromptTemplate_ChatCompletionPrompts.cs`
- `FunctionCalling/Gemini_FunctionCalling.cs` -> `Chat/Gemini_FunctionCalling.cs`
- `Caching/SemanticCachingWithFilters.cs` -> `Filters/Caching_WithFilters.cs`
- `DependencyInjection/HttpClient_Registration.cs` -> `Chat/OpenAI_DependencyInjection_HttpClient_Registration.cs`
- `DependencyInjection/HttpClient_Resiliency.cs` -> `Chat/OpenAI_DependencyInjection_HttpClient_Resiliency.cs`
- `TextToAudio/OpenAI_TextToAudio.cs` -> `Text/OpenAI_TextToAudio.cs`
- `TextToImage/OpenAI_TextToImage.cs` -> `Text/OpenAI_TextToImage.cs`
- `TextGeneration/Ollama_TextGeneration.cs` -> `Text/Ollama_TextGeneration.cs`
- `Memory/TextMemoryPlugin_GeminiEmbeddingGeneration.cs` -> `Plugins/TextMemoryPlugin_GeminiEmbeddingGeneration.cs`
- `Memory/VectorStore_ConsumeFromMemoryStore_AzureAISearch.cs` -> `VectorData/AzureAISearch_VectorStore_ConsumeFromMemoryStore.cs`

### Search Engine for Concept Examples

As a medium term goal, with all the cleanup and restructuring applied, we could consider upgrading the Concepts project to become a flawless and friendly Web Application simply by clicking in the Run button IDE we start it providing an easy WebUI for sample discovery, setup and execution.

To improve easy of access for everyone, we can host the WebApp use it as a link on our official Concepts documentation publishing it as part of the release pipeline, so devs would also be able to easily access our demos without necessarily needing to setup their own envs.

Some of the features we should consider:

- Allow a smart seach by concept and description, ensuring it can index the tests and show them in a HTML or MARKDOWN complying with all the Decision drivers provided above.

- Easy copy/paste. Consolidate all the code for the selected sample in a way that its dependencies are ready to be copied and run into a single Program.cs.

- Enable export to Jupyter Notebook. This would be a great feature to allow users to easily run the samples in their own environment.

## Decision Outcome

TBD
