# Semantic Kernel

[![Python package](https://img.shields.io/pypi/v/semantic-kernel)](https://pypi.org/project/semantic-kernel/)
[![Nuget package](https://img.shields.io/nuget/vpre/Microsoft.SemanticKernel)](https://www.nuget.org/packages/Microsoft.SemanticKernel/)
[![dotnet Docker](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml)
[![dotnet Windows](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml)
[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)
[![Discord](https://img.shields.io/discord/1063152441819942922?label=Discord&logo=discord&logoColor=white&color=d82679)](https://aka.ms/SKDiscord)

> ℹ️ **NOTE**: This project is evolving quickly.
> We invite you to join us in developing the Semantic Kernel together!
> Please contribute by
> using GitHub [Discussions](https://github.com/microsoft/semantic-kernel/discussions),
> opening GitHub [Issues](https://github.com/microsoft/semantic-kernel/issues/new/choose),
> sending us [PRs](https://github.com/microsoft/semantic-kernel/pulls),
> joining our [Discord community](https://aka.ms/SKDiscord).

[Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/overview/)
is a lightweight SDK that integrates Large Language Models (LLMs) like
[OpenAI](https://platform.openai.com/docs/introduction),
[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service),
and [Hugging Face](https://huggingface.co/)
with conventional programming languages like C# and Python. By doing so, you can
create AI apps that combine the best of both worlds.

## Semantic Kernel orchestrates native and semantic functions

With [plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins), you as a developer can
define [semantic functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/semantic-functions) (functions powered by LLMs)
or [native functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/native-functions) (functions powered by C# or Python)
that can then be orchestrated together by Semantic Kernel.

Once you've defined your plugins, Semantic Kernel makes it easy to
[mix-and-match functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions)
from your plugins into a single pipeline with only a few lines of code:

```csharp
var output = await kernel.RunAsync(
    "What is the sum of 2 and 3?",
    GetNumbers,         // Use a semantic function to extract numbers from the question
    AddNumbers          // Use a native function to add the numbers together
);
```

```python
output = await self._kernel.run_async(
    get_numbers,        # Use a semantic function to extract numbers from the question
    add_numbers,        # Use a native function to add the numbers together
    input_str="What is the sum of 2 and 3?",
)
```

Behind the scenes, Semantic Kernel will call your plugins in the order you specified,
and pass the output of one plugin as the input to the next plugin.

## Automatically orchestrate your plugins with planners

What makes Semantic Kernel _special_, however, is its ability to _automatically_ orchestrate
[plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins) with AI.
With [planners](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner), you
can ask an LLM to generate a plan that achieves a user's unique goal. Afterwards, you can ask
Semantic Kernel to execute the plan.

In the [planner example from our docs](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner),
we demonstrate just how easy it is to import a plugin, generate a plan, and then execute a plan:

```csharp
// Add a plugin to the kernel and create a planner
kernel.ImportSkill(new MathPlugin(), "MathPlugin");
var planner = new SequentialPlanner(kernel);

// Ask the planner to create a plan
var ask = "If my investment of 2130.23 dollars increased by 23%, how much would I have after I spent $5 on a latte?";
var plan = await planner.CreatePlanAsync(ask);

// Execute the plan
var result = await plan.InvokeAsync();
```

```python
# Add a plugin to the kernel and create a planner
kernel.import_skill(MathPlugin(), skill_name="math_plugin")
planner = BasicPlanner()

# Ask the planner to create a plan
ask = "If my investment of 2130.23 dollars increased by 23%, how much would I have after I spent $5 on a latte?"
plan = await planner.create_plan_async(ask, kernel)

# Execute the plan
result = await planner.execute_plan_async(plan, kernel)
```

With this code, Semantic Kernel is "smart" enough to know that it should use the provided
`MathPlugin` to multiply `2130.23` by `1.23` and then subtract `5` from the result before
finally returning the answer to the user (`2615.1829`).

## Getting started with Semantic Kernel ⚡

Semantic Kernel is available in a variety of languages and platforms. To get started, choose your preferred language below:

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
        <img align="left" width=52px height=52px src="https://upload.wikimedia.org/wikipedia/en/3/30/Java_programming_language_logo.svg" alt="Java logo">
        <div>
          <a href="https://github.com/microsoft/semantic-kernel/blob/experimental-java/java/README.md">Using Semantic Kernel in Java</a>
        </div>
      </td>
    </tr>
  </tbody>
</table>

See the [Feature Matrix](https://learn.microsoft.com/en-us/semantic-kernel/get-started/supported-languages) to see a breakdown of
feature parity between our currently supported languages.

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

## Learning how to use Semantic Kernel ⚡

For a more hands-on overview, you can also check out the C# and Python Jupyter notebooks, starting
from here:

- [Getting Started with C# notebook](samples/notebooks/dotnet/00-getting-started.ipynb)
- [Getting Started with Python notebook](samples/notebooks/python/00-getting-started.ipynb)

**Requirements:** C# notebooks require [.NET 7](https://dotnet.microsoft.com/download)
and the VS Code [Polyglot extension](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.dotnet-interactive-vscode).

## Chat Copilot

The repository includes some sample applications, with a React frontend and
a backend web service using Semantic Kernel.

Follow the links for more information and instructions about running these apps.

|                                                                         |                                                                                                                                   |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| [Simple chat summary](samples/apps/chat-summary-webapp-react/README.md) | Use ready-to-use plugins and get plugins into your app easily.                                                                    |
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
