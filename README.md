# Semantic Kernel

[![Python package](https://img.shields.io/pypi/v/semantic-kernel)](https://pypi.org/project/semantic-kernel/)
[![Nuget package](https://img.shields.io/nuget/vpre/Microsoft.SemanticKernel)](https://www.nuget.org/packages/Microsoft.SemanticKernel/)
[![dotnet Docker](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml)
[![dotnet Windows](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml)
[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)
[![Discord](https://img.shields.io/discord/1063152441819942922?label=Discord&logo=discord&logoColor=white&color=d82679)](https://aka.ms/SKDiscord)

[Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
is an SDK that integrates Large Language Models (LLMs) like
[OpenAI](https://platform.openai.com/docs/introduction),
[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service),
and [Hugging Face](https://huggingface.co/)
with conventional programming languages like C# and Python. By doing so, you can
create AI apps that combine the best of both worlds.

## Seamlessly integrate LLMs into your existing code ⚡

With [plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins), you can define
[semantic functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/semantic-functions) (functions powered by LLMs)
or [native functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/native-functions) (functions powered by C# or Python)
so that you can seamlessly combine them together with Semantic Kernel. Once you've finished defining your plugins, Semantic Kernel makes it easy to
[mix-and-match functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions)
into a single pipeline with only a [few lines of code](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions?tabs=Csharp#using-the-runasync-method-to-simplify-your-code).

What makes Semantic Kernel _special_, however, is its ability to _automatically_ orchestrate
[plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins) with AI.
With [planners](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner), you
can ask an LLM to generate a plan that achieves a user's unique goal. Afterwards,
Semantic Kernel will execute the plan.

![Orchestrating plugins with planner](https://learn.microsoft.com/en-us/semantic-kernel/media/kernel-infographic.png)

## Getting started with Semantic Kernel ⚡

Semantic Kernel is available in a variety of languages and platforms. To get started, choose your preferred language below. See the [Feature Matrix](https://learn.microsoft.com/en-us/semantic-kernel/get-started/supported-languages) to see a breakdown of
feature parity between our currently supported languages.

<table width=100%>
  <tbody>
    <tr>
      <td>
        <img align="left" width=52px src="https://user-images.githubusercontent.com/371009/230673036-fad1e8e6-5d48-49b1-a9c1-6f9834e0d165.png">
        <div>
          <a href="dotnet/README.md">Using Semantic Kernel in C#</a> &nbsp<br/>
          <a href="https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel?view=semantic-kernel-dotnet">C# reference documentation</a> &nbsp
        </div>
      </td>
      <td>
        <img align="left" width=52px src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg">
        <div>
          <a href="python/README.md">Using Semantic Kernel in Python</a>
        </div>
      </td>
      <td>
        <img align="left" width=52px height=52px src="https://upload.wikimedia.org/wikipedia/en/3/30/Java_programming_language_logo.svg" alt="Java logo">
        <div>
          <a href="https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/README.md">Using Semantic Kernel in Java</a>
        </div>
      </td>
    </tr>
  </tbody>
</table>

The quickest way to get started with the basics is to get an API key
from either OpenAI or Azure OpenAI and to run one of the C#, Python, and Java console applications/scripts below.

### For C#:

1. Create a new console app.
2. Add the semantic kernel nuget `Microsoft.SemanticKernel`.
3. Copy the code from [here](dotnet/README.md) into the app `Program.cs` file.
4. Replace the configuration placeholders for API key and other params with your key and settings.
5. Run with `F5` or `dotnet run`

### For Python:

1. Install the pip package: `python -m pip install semantic-kernel`.
2. Create a new script e.g. `hello-world.py`.
3. Store your API key and settings in an `.env` file as described [here](python/README.md).
4. Copy the code from [here](python/README.md) into the `hello-world.py` script.
5. Run the python script.

### For Java:

1. Clone the repository: `git clone https://github.com/microsoft/semantic-kernel.git`
2. Switch to `semantic-kernel` directory and then checkout experimental Java branch: `git checkout experimental-java`
3. Follow the instructions [here](https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/samples/sample-code/README.md)

## Learning how to use Semantic Kernel ⚡

For a quick guide, you can check out the C# and Python Jupyter notebooks. These notebooks
demonstrate how to use Semantic Kernel with code snippets that you can easily run inline.

- [Getting Started with C# notebook](samples/notebooks/dotnet/00-getting-started.ipynb)
- [Getting Started with Python notebook](samples/notebooks/python/00-getting-started.ipynb)

**Requirements:** C# notebooks require [.NET 7](https://dotnet.microsoft.com/download)
and the VS Code [Polyglot extension](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.dotnet-interactive-vscode).

Once you've finished the getting started notebooks, you can check out the main walkthroughs
on our Learn site:

1. 📖 [Overview of the kernel](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/)
1. 🔌 [Understanding AI plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins)
1. 👄 [Creating semantic functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/semantic-functions)
1. 💽 [Creating native functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/native-functions)
1. ⛓️ [Chaining functions together](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions)
1. 🤖 [Auto create plans with planner](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner)
1. 💡 [Create and run a ChatGPT plugin](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chatgpt-plugins)

## Chat Copilot: see what's possible with Semantic Kernel ⚡

If you're interested in seeing a full end-to-end example of how to use Semantic Kernel, check out
our [Chat Copilot](https://github.com/microsoft/chat-copilot) reference application. Chat Copilot
is a chatbot that demonstrates the power of Semantic Kernel. By combining memory, planning, and
AI plugins, Chat Copilot can have a conversation with you about any topic and autocomplete tasks.

![Chat Copilot answering a question](https://learn.microsoft.com/en-us/semantic-kernel/media/chat-copilot-in-action.gif)

You can find it's repo by navigating to [github.com/microsoft/chat-copilot](https://github.com/microsoft/chat-copilot).
You can also learn more about Chat Copilot in our [documentation](https://learn.microsoft.com/en-us/semantic-kernel/chat-copilot/).

## Check out our other repos! ⚡

If you like Semantic Kernel, you may also be interested in other repos the Semantic Kernel team supports:

| Repo                                                                              | Description                                                                                   |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [Chat Copilot](https://github.com/microsoft/chat-copilot)                         | A reference application that demonstrates how to build a chatbot with Semantic Kernel.        |
| [Semantic Kernel Docs](https://github.com/MicrosoftDocs/semantic-kernel-docs)     | The home for Semantic Kernel documentation that appears on the Microsoft learn site.          |
| [Semantic Kernel Starters](https://github.com/microsoft/semantic-kernel-starters) | Starter projects for Semantic Kernel to make it easier to get started.                        |
| [Semantic Memory](https://github.com/microsoft/semantic-memory)                   | A service that allows you to create pipelines for ingesting, storing, and querying knowledge. |

## Joining the community

We welcome your contributions and suggestions to SK community! One of the easiest
ways to participate is to engage in discussions in the GitHub repository.
Bug reports and fixes are welcome!

For new features, components, or extensions, please open an issue and discuss with
us before sending a PR. This is to avoid rejection as we might be taking the core
in a different direction, but also to consider the impact on the larger ecosystem.

To learn more and get started:

- Read the [documentation](https://aka.ms/sk/learn)
- Learn how to [contribute](https://learn.microsoft.com/en-us/semantic-kernel/get-started/contributing) to the project
- Join the [Discord community](https://aka.ms/SKDiscord)
- Attend [regular office hours and SK community events](COMMUNITY.md)
- Follow the team on our [blog](https://aka.ms/sk/blog)

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
