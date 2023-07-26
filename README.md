# Semantic Kernel

[![Python package](https://img.shields.io/pypi/v/semantic-kernel)](https://pypi.org/project/semantic-kernel/)
[![Nuget package](https://img.shields.io/nuget/vpre/Microsoft.SemanticKernel)](https://www.nuget.org/packages/Microsoft.SemanticKernel/)
[![dotnet Docker](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml)
[![dotnet Windows](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml)
[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)
[![Discord](https://img.shields.io/discord/1063152441819942922?label=Discord&logo=discord&logoColor=white&color=d82679)](https://aka.ms/SKDiscord)

> ℹ️ **NOTE**: This project is just like AI and will evolve quickly.
> We invite you to join us in developing the Semantic Kernel together!
> Please contribute by
> using GitHub [Discussions](https://github.com/microsoft/semantic-kernel/discussions),
> opening GitHub [Issues](https://github.com/microsoft/semantic-kernel/issues/new/choose),
> sending us [PRs](https://github.com/microsoft/semantic-kernel/pulls),
> joining our [Discord community](https://aka.ms/SKDiscord).

**Semantic Kernel (SK)** is a lightweight SDK enabling integration of AI Large
Language Models (LLMs) with conventional programming languages. The SK extensible
programming model combines natural language **semantic functions**, traditional
code **native functions**, and **embeddings-based memory** unlocking new potential
and adding value to applications with AI.

SK supports
[prompt templating](docs/PROMPT_TEMPLATE_LANGUAGE.md), function
chaining,
[vectorized memory](docs/EMBEDDINGS.md), and
[intelligent planning](docs/PLANNERS.md)
capabilities out of the box.

Semantic Kernel supports and encapsulates several design patterns from the latest
in AI research, such that developers can infuse their applications with  [plugins](https://learn.microsoft.com/semantic-kernel/howto/) like [prompt](docs/PROMPT_TEMPLATE_LANGUAGE.md)
chaining, recursive reasoning, summarization, zero/few-shot learning, contextual
memory, long-term memory, [embeddings](docs/EMBEDDINGS.md), semantic indexing,
[planning](docs/PLANNERS.md), retrieval-augmented generation and accessing external
knowledge stores as well as your own data.

By joining the SK community, you can build AI-first apps faster and have a front-row
peek at how the SDK is being built. SK has been released as open-source so that more
pioneering developers can join us in crafting the future of this landmark moment
in the history of computing.

## Get Started with Semantic Kernel ⚡

Semantic Kernel is available to explore AI and build apps with C#, Python and Java:

<table width=100%>
  <tbody>
    <tr>
      <td>
        <img align="left" width=52px src="https://user-images.githubusercontent.com/371009/230673036-fad1e8e6-5d48-49b1-a9c1-6f9834e0d165.png">
        <div>
          <a href="dotnet/README.md">Using Semantic Kernel in C#</a> &nbsp
        </div>
      </td>
      <td>
        <img align="left" width=52px src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg">
        <div>
          <a href="python/README.md">Using Semantic Kernel in Python</a>
        </div>
      </td>
      <td>
        <img align="left" width=52px src="https://en.wikipedia.org/wiki/Java_(programming_language)#/media/File:Java_programming_language_logo.svg">
        <div>
          <a href="https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/README.md">Using Semantic Kernel in Java</a>
        </div>
      </td>
    </tr>
  </tbody>
</table>

See the [Feature Matrix](https://learn.microsoft.com/en-us/semantic-kernel/get-started/supported-languages) to see a breakdown of feature parity between our currently supported languages.

The quickest way to get started with the basics is to get an API key
(OpenAI or Azure OpenAI)
and to run one of the C#, Python, and Java console applications/scripts:

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

## Sample apps ⚡

The repository includes some sample applications, with a React frontend and
a backend web service using Semantic Kernel.

Follow the links for more information and instructions about running these apps.

|                                                                         |                                                                                                                                   |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [Simple chat summary](samples/apps/chat-summary-webapp-react/README.md) | Use ready-to-use plugins and get plugins into your app easily.                                                                |
| [Book creator](samples/apps/book-creator-webapp-react/README.md)        | Use planner to deconstruct a complex goal and envision using the planner in your app.                                             |
| [Authentication and APIs](samples/apps/auth-api-webapp-react/README.md) | Use a basic connector pattern to authenticate and connect to an API and imagine integrating external data into your app's LLM AI. |
| [GitHub repository Q&A](samples/apps/github-qna-webapp-react/README.md) | Use embeddings and memory to store recent data and allow you to query against it.                                                 |
| [Copilot Chat Sample App](samples/apps/copilot-chat-app/README.md)      | Build your own chat experience based on Semantic Kernel.                                                                          |

**Requirements:**

- You will need an
  [Open AI API Key](https://openai.com/api/) or
  [Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)
  to get started.
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
  are required to run the kernel as a local web service, used by the sample web apps.
- [.NET 6 SDK](https://dotnet.microsoft.com/download/dotnet/6.0) or [.NET 7 SDK](https://dotnet.microsoft.com/download/dotnet/7.0)
- [Yarn](https://yarnpkg.com/getting-started/install) is used for installing web apps' dependencies.

## Deploy Semantic Kernel to Azure in a web app service ☁️

Getting Semantic Kernel deployed to Azure as web app service is easy with one-click deployments. Click [here](https://aka.ms/sk-docs-azuredeploy) to learn more on how to deploy to Azure.

## Jupyter Notebooks ⚡

For a more hands-on overview, you can also check out the C# and Python Jupyter notebooks, starting
from here:
* [Getting Started with C# notebook](samples/notebooks/dotnet/00-getting-started.ipynb)
* [Getting Started with Python notebook](samples/notebooks/python/00-getting-started.ipynb)

**Requirements:** C# notebooks require [.NET 7](https://dotnet.microsoft.com/download)
and the VS Code [Polyglot extension](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.dotnet-interactive-vscode).

## Contributing and Community

We welcome your contributions and suggestions to SK community! One of the easiest
ways to participate is to engage in discussions in the GitHub repository.
Bug reports and fixes are welcome!

For new features, components, or extensions, please open an issue and discuss with
us before sending a PR. This is to avoid rejection as we might be taking the core
in a different direction, but also to consider the impact on the larger ecosystem.

To learn more and get started:

- Read the [documentation](https://aka.ms/sk/learn)
- Learn how to [contribute](https://github.com/microsoft/semantic-kernel/blob/main/CONTRIBUTING.md) to the project
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
