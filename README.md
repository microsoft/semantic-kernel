# Semantic Kernel

[![dotnet](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci.yml)

**Semantic Kernel (SK)** is a lightweight SDK enabling integration of AI Large
Language Models (LLMs) with conventional programming languages. The SK extensible
programming model combines natural language **semantic functions**, traditional
code **native functions**, and **embeddings-based memory** unlocking new potential
and adding value to applications with AI.

SK supports
[prompt templating](docs/PROMPT_TEMPLATE_LANGUAGE.md), function
chaining,
[vectorized memory](docs/EMBEDDINGS.md), and
[intelligent planning](docs/PLANNER.md)
capabilities out of the box.

![image](https://user-images.githubusercontent.com/371009/221739773-cf43522f-c1e4-42f2-b73d-5ba84e21febb.png)

Semantic Kernel is designed to support and encapsulate several design patterns from the
latest in AI research, such that developers can infuse their applications with complex
[skills](docs/SKILLS.md) like [prompt](docs/PROMPT_TEMPLATE_LANGUAGE.md) chaining,
recursive reasoning, summarization, zero/few-shot learning, contextual memory,
long-term memory, [embeddings](docs/EMBEDDINGS.md), semantic indexing, [planning](docs/PLANNER.md),
and accessing external knowledge stores as well as your own data.

By joining the SK community, you can build AI-first apps faster and have a front-row
peek at how the SDK is being built. SK has been released as open-source so that more
pioneering developers can join us in crafting the future of this landmark moment
in the history of computing.

## Samples ⚡

If you would like a quick overview about how Semantic Kernel can integrate with your
app, start by cloning the repository:

```shell
git clone https://github.com/microsoft/semantic-kernel.git
```

and try these examples:

|                                                                         |                                                                                                                                   |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [Simple chat summary](samples/apps/chat-summary-webapp-react/README.md) | Use ready-to-use skills and get those skills into your app easily.                                                                |
| [Book creator](samples/apps/book-creator-webapp-react/README.md)        | Use planner to deconstruct a complex goal and envision using the planner in your app.                                             |
| [Authentication and APIs](samples/apps/auth-api-webapp-react/README.md) | Use a basic connector pattern to authenticate and connect to an API and imagine integrating external data into your app's LLM AI. |

For a more hands-on overview, you can also run the
[Getting Started notebook](samples/notebooks/dotnet/Getting-Started-Notebook.ipynb),
looking into the syntax, creating
[Semantic Functions](docs/GLOSSARY.md),
working with Memory, and see how the kernel works.

**Please note:**

- You will need an
  [Open AI API Key](https://openai.com/api/) or
  [Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)
  to get started.
- There are a few software requirements you may need to satisfy before running examples and notebooks:
  1. [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
     used for running the kernel as a local API, required by the web apps.
  2. [Yarn](https://yarnpkg.com/getting-started/install) used for installing
     web apps' dependencies.
  3. Semantic Kernel supports .NET Standard 2.1 and it's recommended using .NET 6+. However, some of
     the examples in the repository require [.NET 7](https://dotnet.microsoft.com/download) and the VS Code
     [Polyglot extension](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.dotnet-interactive-vscode)
     to run the notebooks.

## Get Started with Semantic Kernel ⚡

Here is a quick example of how to use Semantic Kernel from a C# console app.

1.  Create a new project, targeting .NET 6 or newer, and add the
    `Microsoft.SemanticKernel` nuget package:

        dotnet add package Microsoft.SemanticKernel --version <version number>

    See [nuget.org](https://www.nuget.org/packages/Microsoft.SemanticKernel/) for
    the latest version and more instructions.

2.  Copy and paste the following code into your project, with your Azure OpenAI
    key in hand (you can create one
    [here](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)).

```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;

var kernel = Kernel.Builder.Build();

kernel.Config.AddAzureOpenAICompletionBackend(
    "davinci-backend",                   // Alias used by the kernel
    "text-davinci-003",                  // Azure OpenAI *Deployment ID*
    "https://contoso.openai.azure.com/", // Azure OpenAI *Endpoint*
    "...your Azure OpenAI Key..."        // Azure OpenAI *Key*
);

string skPrompt = @"
{{$input}}

Give me the TLDR in 5 words.
";

string textToSummarize = @"
1) A robot may not injure a human being or, through inaction,
allow a human being to come to harm.

2) A robot must obey orders given it by human beings except where
such orders would conflict with the First Law.

3) A robot must protect its own existence as long as such protection
does not conflict with the First or Second Law.
";

var tldrFunction = kernel.CreateSemanticFunction(skPrompt);

var summary = await kernel.RunAsync(textToSummarize, tldrFunction);

Console.WriteLine(summary);

// Output => Protect humans, follow orders, survive.
```

## Contributing and Community

We welcome your contributions and suggestions to SK community! One of the easiest
ways to participate is to engage in discussions in the GitHub repository.
Bug reports and fixes are welcome!

For new features, components, or extensions, please open an issue and discuss with
us before sending a PR. This is to avoid rejection as we might be taking the core
in a different direction, but also to consider the impact on the larger ecosystem.

To learn more and get started, please read our [Contributing page](CONTRIBUTING.md)
and check some of our documentation:

- [SK Prompt Template Language](docs/PROMPT_TEMPLATE_LANGUAGE.md)
- [SKills and Functions](docs/SKILLS.md)
- [Embeddings and Semantic Memory](docs/EMBEDDINGS.md)
- [SK Planner](docs/PLANNER.md)
- [SK Notebooks](samples/notebooks/dotnet/README.md)

## Code of Conduct

This project has adopted the
[Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the
[Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
or contact [opencode@microsoft.com](mailto:opencode@microsoft.com)
with any additional questions or comments.

## License

Copyright (c) Microsoft Corporation. All rights reserved.

Licensed under the [MIT](LICENSE) license.
