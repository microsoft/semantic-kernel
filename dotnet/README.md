# Get Started with Semantic Kernel ⚡

## OpenAI / Azure OpenAI API keys

To run the LLM prompts and semantic functions in the examples below, make sure
you have an

- [Azure OpenAI Service Key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api) or
- [OpenAI API Key](https://platform.openai.com).

## Nuget package

Here is a quick example of how to use Semantic Kernel from a C# console app.
First, let's create a new project, targeting .NET 6 or newer, and add the
`Microsoft.SemanticKernel` nuget package to your project from the command prompt
in Visual Studio:

    dotnet add package Microsoft.SemanticKernel

# Running prompts with input parameters

Copy and paste the following code into your project, with your Azure OpenAI key in hand:

```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

var builder = Kernel.CreateBuilder();

builder.AddAzureOpenAIChatCompletion(
         "gpt-35-turbo",                      // Azure OpenAI Deployment Name
         "https://contoso.openai.azure.com/", // Azure OpenAI Endpoint
         "...your Azure OpenAI Key...");      // Azure OpenAI Key

// Alternative using OpenAI
//builder.AddOpenAIChatCompletion(
//         "gpt-3.5-turbo",                  // OpenAI Model name
//         "...your OpenAI API Key...");     // OpenAI API Key

var kernel = builder.Build();

var prompt = @"{{$input}}

One line TLDR with the fewest words.";

var summarize = kernel.CreateFunctionFromPrompt(prompt, executionSettings: new OpenAIPromptExecutionSettings { MaxTokens = 100 });

string text1 = @"
1st Law of Thermodynamics - Energy cannot be created or destroyed.
2nd Law of Thermodynamics - For a spontaneous process, the entropy of the universe increases.
3rd Law of Thermodynamics - A perfect crystal at zero Kelvin has zero entropy.";

string text2 = @"
1. An object at rest remains at rest, and an object in motion remains in motion at constant speed and in a straight line unless acted on by an unbalanced force.
2. The acceleration of an object depends on the mass of the object and the amount of force applied.
3. Whenever one object exerts a force on another object, the second object exerts an equal and opposite on the first.";

Console.WriteLine(await kernel.InvokeAsync(summarize, new() { ["input"] = text1 }));

Console.WriteLine(await kernel.InvokeAsync(summarize, new() { ["input"] = text2 }));

// Output:
//   Energy conserved, entropy increases, zero entropy at 0K.
//   Objects move in response to forces.
```

# Semantic Kernel Notebooks

The repository contains also a few C# Jupyter notebooks that demonstrates
how to get started with the Semantic Kernel.

See [here](./notebooks/README.md) for the full list, with
requirements and setup instructions.

1. [Getting started](./notebooks/00-getting-started.ipynb)
2. [Loading and configuring Semantic Kernel](./notebooks/01-basic-loading-the-kernel.ipynb)
3. [Running AI prompts from file](./notebooks/02-running-prompts-from-file.ipynb)
4. [Creating Semantic Functions at runtime (i.e. inline functions)](./notebooks/03-semantic-function-inline.ipynb)
5. [Using Kernel Arguments to Build a Chat Experience](./notebooks/04-kernel-arguments-chat.ipynb)
6. [Introduction to the Planning/Function Calling](./notebooks/05-using-function-calling.ipynb)
7. [Building Memory with Embeddings](./notebooks/06-memory-and-embeddings.ipynb)
8. [Creating images with DALL-E 3](./notebooks/07-DALL-E-3.ipynb)
9. [Chatting with ChatGPT and Images](./notebooks/08-chatGPT-with-DALL-E-3.ipynb)
10. [BingSearch using Kernel](./notebooks/10-RAG-with-BingSearch.ipynb)

# Semantic Kernel Samples

The repository also contains the following code samples:

| Type                                                                       | Description                                                                                                            |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| [`GettingStarted`](./samples/GettingStarted/README.md)                     | Take this step by step tutorial to get started with the Semantic Kernel and get introduced to the key concepts.        |
| [`GettingStartedWithAgents`](./samples/GettingStartedWithAgents/README.md) | Take this step by step tutorial to get started with the Semantic Kernel Agents and get introduced to the key concepts. |
| [`Concepts`](./samples/Concepts/README.md)                                 | This section contains focussed samples which illustrate all of the concepts included in the Semantic Kernel.           |
| [`Demos`](./samples/Demos/README.md)                                       | Look here to find a sample which demonstrates how to use many of Semantic Kernel features.                              |
| [`LearnResources`](./samples/LearnResources/README.md)                     | Code snippets that are related to online documentation sources like Microsoft Learn, DevBlogs and others               |

# Nuget packages

Semantic Kernel provides a set of nuget packages to allow extending the core with
more features, such as connectors to services and plugins to perform specific actions.
Unless you need to optimize which packages to include in your app, you will usually
start by installing this meta-package first:

- **Microsoft.SemanticKernel**

This meta package includes core packages and OpenAI connectors, allowing to run
most samples and build apps with OpenAI and Azure OpenAI.

Packages included in **Microsoft.SemanticKernel**:

1. **Microsoft.SemanticKernel.Abstractions**: contains common interfaces and classes
   used by the core and other SK components.
1. **Microsoft.SemanticKernel.Core**: contains the core logic of SK, such as prompt
   engineering, semantic memory and semantic functions definition and orchestration.
1. **Microsoft.SemanticKernel.Connectors.OpenAI**: connectors to OpenAI and Azure
   OpenAI, allowing to run semantic functions, chats, text to image with GPT3,
   GPT3.5, GPT4, DALL-E3.

Other SK packages available at nuget.org:

1. **Microsoft.SemanticKernel.Connectors.Qdrant**: Qdrant connector for
   plugins and semantic memory.
2. **Microsoft.SemanticKernel.Connectors.Sqlite**: SQLite connector for
   plugins and semantic memory
3. **Microsoft.SemanticKernel.Plugins.Document**: Document Plugin: Word processing,
   OpenXML, etc.
4. **Microsoft.SemanticKernel.Plugins.MsGraph**: Microsoft Graph Plugin: access your
   tenant data, schedule meetings, send emails, etc.
5. **Microsoft.SemanticKernel.Plugins.OpenApi**: OpenAPI Plugin.
6. **Microsoft.SemanticKernel.Plugins.Web**: Web Plugin: search the web, download
   files, etc.
