# Semantic Kernel

## Status

- Python <br/>
  [![Python package](https://img.shields.io/pypi/v/semantic-kernel)](https://pypi.org/project/semantic-kernel/)
- .NET <br/>
  [![Nuget package](https://img.shields.io/nuget/vpre/Microsoft.SemanticKernel)](https://www.nuget.org/packages/Microsoft.SemanticKernel/)[![dotnet Docker](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml)[![dotnet Windows](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml)
- Java <br/>
  [![Java CICD Builds](https://github.com/microsoft/semantic-kernel/actions/workflows/java-build.yml/badge.svg?branch=java-development)](https://github.com/microsoft/semantic-kernel/actions/workflows/java-build.yml)[![Maven Central](https://maven-badges.herokuapp.com/maven-central/com.microsoft.semantic-kernel/semantickernel-api/badge.svg)](https://maven-badges.herokuapp.com/maven-central/com.microsoft.semantic-kernel/semantickernel-api)

## Overview

[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)
[![Discord](https://img.shields.io/discord/1063152441819942922?label=Discord&logo=discord&logoColor=white&color=d82679)](https://aka.ms/SKDiscord)

[Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
is an SDK that integrates Large Language Models (LLMs) like
[OpenAI](https://platform.openai.com/docs/introduction),
[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service),
and [Hugging Face](https://huggingface.co/)
with conventional programming languages like C#, Python, and Java. Semantic Kernel achieves this
by allowing you to define [plugins](https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins)
that can be chained together
in just a [few lines of code](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions?tabs=Csharp#using-the-runasync-method-to-simplify-your-code).

What makes Semantic Kernel _special_, however, is its ability to _automatically_ orchestrate
plugins with AI. With Semantic Kernel
[planners](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner), you
can ask an LLM to generate a plan that achieves a user's unique goal. Afterwards,
Semantic Kernel will execute the plan for the user.

It provides:

- abstractions for AI services (such as chat, text to images, audio to text, etc.) and memory stores
- implementations of those abstractions for services from [OpenAI](https://platform.openai.com/docs/introduction), [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service), [Hugging Face](https://huggingface.co/), local models, and more, and for a multitude of vector databases, such as those from [Chroma](https://docs.trychroma.com/getting-started), [Qdrant](https://qdrant.tech/), [Milvus](https://milvus.io/), and [Azure](https://learn.microsoft.com/en-us/azure/search/search-what-is-azure-search)
- a common representation for [plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins), which can then be orchestrated automatically by AI
- the ability to create such plugins from a multitude of sources, including from OpenAPI specifications, prompts, and arbitrary code written in the target language
- extensible support for prompt management and rendering, including built-in handling of common formats like Handlebars and Liquid
- and a wealth of functionality layered on top of these abstractions, such as filters for responsible AI, dependency injection integration, and more.

Semantic Kernel is utilized by enterprises due to its flexibility, modularity and observability. Backed with security enhancing capabilities like telemetry support, and hooks and filters so you’ll feel confident you’re delivering responsible AI solutions at scale.
Semantic Kernel was designed to be future proof, easily connecting your code to the latest AI models evolving with the technology as it advances. When new models are released, you’ll simply swap them out without needing to rewrite your entire codebase.

#### Please star the repo to show your support for this project!

![Enterprise-ready](https://learn.microsoft.com/en-us/semantic-kernel/media/enterprise-ready.png)

## Getting started with Semantic Kernel

The Semantic Kernel SDK is available in C#, Python, and Java. To get started, choose your preferred language below. See the [Feature Matrix](https://learn.microsoft.com/en-us/semantic-kernel/get-started/supported-languages) to see a breakdown of
feature parity between our currently supported languages.

<table width=100%>
  <tbody>
    <tr>
      <td>
        <img align="left" width=52px src="https://user-images.githubusercontent.com/371009/230673036-fad1e8e6-5d48-49b1-a9c1-6f9834e0d165.png">
        <div>
          <a href="dotnet/README.md">Using Semantic Kernel in C#</a> &nbsp<br/>
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
          <a href="https://github.com/microsoft/semantic-kernel/blob/main/java/README.md">Using Semantic Kernel in Java</a>
        </div>
      </td>
    </tr>
  </tbody>
</table>

The quickest way to get started with the basics is to get an API key
from either OpenAI or Azure OpenAI and to run one of the C#, Python, and Java console applications/scripts below.

### For C#:

1. Go to the Quick start page [here](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-csharp) and follow the steps to dive in.
2. After Installing the SDK, we advise you follow the steps and code detailed to write your first console app.
   ![dotnetmap](https://learn.microsoft.com/en-us/semantic-kernel/media/dotnetmap.png)

### For Python:

1. Go to the Quick start page [here](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python) and follow the steps to dive in.
2. You'll need to ensure that you toggle to C# in the the Choose a programming language table at the top of the page.
   ![pythonmap](https://learn.microsoft.com/en-us/semantic-kernel/media/pythonmap.png)

### For Java:

The Java code is in the [semantic-kernel-java](https://github.com/microsoft/semantic-kernel-java) repository. See
[semantic-kernel-java build](https://github.com/microsoft/semantic-kernel-java/blob/main/BUILD.md) for instructions on
how to build and run the Java code.

Please file Java Semantic Kernel specific issues in
the [semantic-kernel-java](https://github.com/microsoft/semantic-kernel-java) repository.

## Learning how to use Semantic Kernel

The fastest way to learn how to use Semantic Kernel is with our C# and Python Jupyter notebooks. These notebooks
demonstrate how to use Semantic Kernel with code snippets that you can run with a push of a button.

- [Getting Started with C# notebook](dotnet/notebooks/00-getting-started.ipynb)
- [Getting Started with Python notebook](python/samples/getting_started/00-getting-started.ipynb)

Once you've finished the getting started notebooks, you can then check out the main walkthroughs
on our Learn site. Each sample comes with a completed C# and Python project that you can run locally.

1. 📖 [Getting Started](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)
1. 🔌 [Detailed Samples](https://learn.microsoft.com/en-us/semantic-kernel/get-started/detailed-samples)
1. 💡 [Concepts](https://learn.microsoft.com/en-us/semantic-kernel/concepts/agents)

Finally, refer to our API references for more details on the C# and Python APIs:

- [C# API reference](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel?view=semantic-kernel-dotnet)
- [Python API reference](https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel-python)
- Java API reference (coming soon)

## Visual Studio Code extension: design semantic functions with ease

The Semantic Kernel extension for Visual Studio Code makes it easy to design and test semantic functions. The extension provides an interface for designing semantic functions and allows you to test them with the push of a button with your existing models and data.

## Join the community

We welcome your contributions and suggestions to SK community! One of the easiest
ways to participate is to engage in discussions in the GitHub repository.
Bug reports and fixes are welcome!

For new features, components, or extensions, please open an issue and discuss with
us before sending a PR. This is to avoid rejection as we might be taking the core
in a different direction, but also to consider the impact on the larger ecosystem.

To learn more and get started:

- Read the [documentation](https://aka.ms/sk/learn)
- Learn how to [contribute](https://learn.microsoft.com/en-us/semantic-kernel/get-started/contributing) to the project
- Ask questions in the [GitHub discussions](https://github.com/microsoft/semantic-kernel/discussions)
- Ask questions in the [Discord community](https://aka.ms/SKDiscord)

- Attend [regular office hours and SK community events](COMMUNITY.md)
- Follow the team on our [blog](https://aka.ms/sk/blog)

## Contributor Wall of Fame

[![semantic-kernel contributors](https://contrib.rocks/image?repo=microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/graphs/contributors)

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
