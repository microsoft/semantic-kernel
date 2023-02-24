# Semantic Kernel

[![dotnet](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci.yml)

This repository is where we (Microsoft) develop the Semantic Kernel product together with you, the community.

## About Semantic Kernel

Semantic Kernel is a lightweight SDK that offers a simple, powerful, and consistent programming model mixing
traditional code with AI and "semantic" functions, covering multiple programming languages and platforms.

Semantic Kernel is designed to support and encapsulate several design patterns from the latest in AI research
such that developers can infuse their applications with complex skills like prompt chaining, recursive reasoning,
summarization, zero/few-shot learning, contextual memory, long-term memory, embeddings, semantic indexing,
planning, and accessing external knowledge stores as well as your own data.

## Getting Started ⚡

To get started with Semantic Kernel, you can clone the semantic-kernel repository:

```shell
git clone https://github.com/microsoft/semantic-kernel.git
```

And then run the [getting started notebook](samples/notebooks/dotnet/Getting-Started-Notebook.ipynb)
or try the samples:

- [Simple chat summary](samples/apps/chat-summary-webapp-react/README.md) (**Recommended**)
- [Book creator](samples/apps/book-creator-webapp-react/README.md)
- [Authentication and APIs](samples/apps/auth-api-webapp-react/README.md)

Alternatively, you can also can create a C# app that uses the SDK (see next section).

**IMPORTANT** - You will need an [Open AI Key](https://openai.com/api/) or
[Azure Open AI Service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)
to get started.

**IMPORTANT** - There are [software requirements](https://aka.ms/SK-Requirements)
you may need to satisfy for running the samples and notebooks.

## Use Semantic Kernel in a C# Console App

Here is a quick example of how to use Semantic Kernel from a C# app.

Create a new project targeting .NET 3.1 or newer, and add the
`Microsoft.SemanticKernel` nuget package.

Copy and paste the following code into your project, with your Azure OpenAI
key in hand. If you need to create one, go
[here](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api).

```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;

var kernel = Kernel.Builder.Build();

kernel.Config.AddAzureOpenAICompletionBackend(
    "azure_davinci",                     // Internal alias
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

There are many ways in which you can participate in this project:

- [Contribute](CONTRIBUTING.md) to the project
- Submit [Issues](https://github.com/microsoft/semantic-kernel/issues)
- Join the [Discord community](https://aka.ms/SKDiscord)
- Learn more at the [documentation site](https://aka.ms/SK-Docs)

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
