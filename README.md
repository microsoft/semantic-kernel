<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< HEAD
---
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
<<<<<<< HEAD
---
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
---
title: SK Api
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
app_port: 3000
suggested_hardware: a10g-small
license: other
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
license: apache-2.0
datasets:
- Bryan-Roe/Dataset
language:
- en
metrics:
- accuracy
- code_eval
base_model:
- Bryan-Roe/SK-api
new_version: Bryan-Roe/SK-api
---
# Model Card for Model ID
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
runme:
  id: 01J0BYQX0015D3BH4FX0NPA9QQ
  version: v3
---

# Semantic Kernel

## Status

- Python <br/>
  [![Python package](https://img.shields.io/pypi/v/semantic-kernel)](https://pypi.org/project/semantic-kernel/)
- .NET <br/>
  [![Nuget package](https://img.shields.io/nuget/vpre/Microsoft.SemanticKernel)](https://www.nuget.org/packages/Microsoft.SemanticKernel/)[![dotnet Docker](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-docker.yml)[![dotnet Windows](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml/badge.svg?branch=main)](https://github.com/microsoft/semantic-kernel/actions/workflows/dotnet-ci-windows.yml)

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

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
It provides:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
It provides:
=======
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
#### Please star the repo to show your support for this project

- abstractions for AI services (such as chat, text to images, audio to text, etc.) and memory stores
- implementations of those abstractions for services from [OpenAI](https://platform.openai.com/docs/introduction), [Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service), [Hugging Face](https://huggingface.co/), local models, and more, and for a multitude of vector databases, such as those from [Chroma](https://docs.trychroma.com/getting-started), [Qdrant](https://qdrant.tech/), [Milvus](https://milvus.io/), and [Azure](https://learn.microsoft.com/en-us/azure/search/search-what-is-azure-search)
- a common representation for [plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins), which can then be orchestrated automatically by AI
- the ability to create such plugins from a multitude of sources, including from OpenAPI specifications, prompts, and arbitrary code written in the target language
- extensible support for prompt management and rendering, including built-in handling of common formats like Handlebars and Liquid
- and a wealth of functionality layered on top of these abstractions, such as filters for responsible AI, dependency injection integration, and more.

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
Semantic Kernel is utilized by enterprises due to its flexibility, modularity and observability. Backed with security enhancing capabilities like telemetry support, and hooks and filters so you’ll feel confident you’re delivering responsible AI solutions at scale.
Semantic Kernel was designed to be future proof, easily connecting your code to the latest AI models evolving with the technology as it advances. When new models are released, you’ll simply swap them out without needing to rewrite your entire codebase.

#### Please star the repo to show your support for this project!

![Enterprise-ready](https://learn.microsoft.com/en-us/semantic-kernel/media/enterprise-ready.png)

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
## Getting started with Semantic Kernel

The Semantic Kernel SDK is available in C#, Python, and Java. To get started, choose your preferred language below. See the [Feature Matrix](https://learn.microsoft.com/en-us/semantic-kernel/get-started/supported-languages) for a breakdown of
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

### For C

1. Go to the Quick start page [here](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-csharp) and follow the steps to dive in.
2. After Installing the SDK, we advise you follow the steps and code detailed to write your first console app.
   ![dotnetmap](https://learn.microsoft.com/en-us/semantic-kernel/media/dotnetmap.png)

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
### For Python

1. Go to the Quick start page [here](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python) and follow the steps to dive in.
2. You'll need to ensure that you toggle to Python in the the Choose a programming language table at the top of the page.
   ![pythonmap](https://learn.microsoft.com/en-us/semantic-kernel/media/pythonmap.png)

### For Java

The Java code is in the [semantic-kernel-java](https://github.com/microsoft/semantic-kernel-java) repository. See
[semantic-kernel-java build](https://github.com/microsoft/semantic-kernel-java/blob/main/BUILD.md) for instructions on
how to build and run the Java code.

Please file Java Semantic Kernel specific issues in
the [semantic-kernel-java](https://github.com/microsoft/semantic-kernel-java) repository.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<!-- Provide a quick summary of what the model is/does. -->

This modelcard aims to be a base template for new models. It has been generated using [this raw template](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/modelcard_template.md?plain=1).

## Model Details

### Model Description
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<!-- Provide a quick summary of what the model is/does. -->

This modelcard aims to be a base template for new models. It has been generated using [this raw template](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/modelcard_template.md?plain=1).

## Model Details

### Model Description
>>>>>>> origin/main
1. Clone the repository: `git clone https://github.com/microsoft/semantic-kernel.git`
   1. To access the latest Java code, clone and checkout the Java development branch: `git clone -b java-development https://github.com/microsoft/semantic-kernel.git`

2. Follow the instructions [here](https://github.com/microsoft/semantic-kernel/blob/main/java/samples/sample-code/README.md)

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
## Learning how to use Semantic Kernel
=======
<!-- Provide a longer summary of what this model is. -->
>>>>>>> origin/main


<<<<<<< head
- [Getting Started with C# notebook](dotnet/notebooks/00-getting-started.ipynb)
- [Getting Started with Python notebook](python/samples/getting_started/00-getting-started.ipynb)
=======
>>>>>>> origin/main

- **Developed by:** [More Information Needed]
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Model type:** [More Information Needed]
- **Language(s) (NLP):** [More Information Needed]
- **License:** [More Information Needed]
- **Finetuned from model [optional]:** [More Information Needed]

<<<<<<< head
1. 📖 [Getting Started](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)
1. 🔌 [Detailed Samples](https://learn.microsoft.com/en-us/semantic-kernel/get-started/detailed-samples)
1. 💡 [Concepts](https://learn.microsoft.com/en-us/semantic-kernel/concepts/agents)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<!-- Provide a longer summary of what this model is. -->


<<<<<<< main
- [Getting Started with C# notebook](dotnet/notebooks/00-getting-started.ipynb)
- [Getting Started with Python notebook](python/samples/getting_started/00-getting-started.ipynb)
=======
>>>>>>> origin/main

- **Developed by:** [More Information Needed]
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Model type:** [More Information Needed]
- **Language(s) (NLP):** [More Information Needed]
- **License:** [More Information Needed]
- **Finetuned from model [optional]:** [More Information Needed]

<<<<<<< main
1. 📖 [Getting Started](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)
1. 🔌 [Detailed Samples](https://learn.microsoft.com/en-us/semantic-kernel/get-started/detailed-samples)
1. 💡 [Concepts](https://learn.microsoft.com/en-us/semantic-kernel/concepts/agents)
=======
### Model Sources [optional]
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
### Model Sources [optional]
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
1. 📖 [Overview of the kernel](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/)
2. 🔌 [Understanding AI plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins)
3. 👄 [Creating semantic functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/semantic-functions)
4. 💽 [Creating native functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/native-functions)
5. ⛓️ [Chaining functions together](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions)
6. 🤖 [Auto create plans with planner](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner)
7. 💡 [Create and run a ChatGPT plugin](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chatgpt-plugins)
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======

<!-- Provide the basic links for the model. -->

- **Repository:** [More Information Needed]
- **Paper [optional]:** [More Information Needed]
- **Demo [optional]:** [More Information Needed]

## Uses

<!-- Address questions around how the model is intended to be used, including the foreseeable users of the model and those affected by the model. -->

### Direct Use

<!-- This section is for the model use without fine-tuning or plugging into a larger ecosystem/app. -->

[More Information Needed]

### Downstream Use [optional]

<!-- This section is for the model use when fine-tuned for a task, or when plugged into a larger ecosystem/app -->

[More Information Needed]

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the model will not work well for. -->

[More Information Needed]

## Bias, Risks, and Limitations

<!-- This section is meant to convey both technical and sociotechnical limitations. -->

[More Information Needed]

### Recommendations

<!-- This section is meant to convey recommendations with respect to the bias, risk, and technical limitations. -->

Users (both direct and downstream) should be made aware of the risks, biases and limitations of the model. More information needed for further recommendations.

## How to Get Started with the Model

Use the code below to get started with the model.

[More Information Needed]

## Training Details

### Training Data

<!-- This should link to a Dataset Card, perhaps with a short stub of information on what the training data is all about as well as documentation related to data pre-processing or additional filtering. -->

[More Information Needed]

### Training Procedure

<!-- This relates heavily to the Technical Specifications. Content here should link to that section when it is relevant to the training procedure. -->

#### Preprocessing [optional]

[More Information Needed]


#### Training Hyperparameters

- **Training regime:** [More Information Needed] <!--fp32, fp16 mixed precision, bf16 mixed precision, bf16 non-mixed precision, fp16 non-mixed precision, fp8 mixed precision -->

#### Speeds, Sizes, Times [optional]

<!-- This section provides information about throughput, start/end time, checkpoint size if relevant, etc. -->

[More Information Needed]

## Evaluation

<!-- This section describes the evaluation protocols and provides the results. -->

### Testing Data, Factors & Metrics

#### Testing Data

<!-- This should link to a Dataset Card if possible. -->

[More Information Needed]

#### Factors

<!-- These are the things the evaluation is disaggregating by, e.g., subpopulations or domains. -->

[More Information Needed]

#### Metrics

<!-- These are the evaluation metrics being used, ideally with a description of why. -->

[More Information Needed]

### Results

[More Information Needed]

#### Summary



## Model Examination [optional]

<!-- Relevant interpretability work for the model goes here -->

[More Information Needed]

## Environmental Impact

<!-- Total emissions (in grams of CO2eq) and additional considerations, such as electricity usage, go here. Edit the suggested text below accordingly -->
>>>>>>> origin/main

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======

<!-- Provide the basic links for the model. -->

- **Repository:** [More Information Needed]
- **Paper [optional]:** [More Information Needed]
- **Demo [optional]:** [More Information Needed]

## Uses

<!-- Address questions around how the model is intended to be used, including the foreseeable users of the model and those affected by the model. -->

### Direct Use

<!-- This section is for the model use without fine-tuning or plugging into a larger ecosystem/app. -->

[More Information Needed]

### Downstream Use [optional]

<!-- This section is for the model use when fine-tuned for a task, or when plugged into a larger ecosystem/app -->

[More Information Needed]

### Out-of-Scope Use

<!-- This section addresses misuse, malicious use, and uses that the model will not work well for. -->

[More Information Needed]

## Bias, Risks, and Limitations

<!-- This section is meant to convey both technical and sociotechnical limitations. -->

[More Information Needed]

### Recommendations

<!-- This section is meant to convey recommendations with respect to the bias, risk, and technical limitations. -->

Users (both direct and downstream) should be made aware of the risks, biases and limitations of the model. More information needed for further recommendations.

## How to Get Started with the Model

Use the code below to get started with the model.

[More Information Needed]

## Training Details

### Training Data

<!-- This should link to a Dataset Card, perhaps with a short stub of information on what the training data is all about as well as documentation related to data pre-processing or additional filtering. -->

[More Information Needed]

### Training Procedure

<!-- This relates heavily to the Technical Specifications. Content here should link to that section when it is relevant to the training procedure. -->

#### Preprocessing [optional]

[More Information Needed]


#### Training Hyperparameters

- **Training regime:** [More Information Needed] <!--fp32, fp16 mixed precision, bf16 mixed precision, bf16 non-mixed precision, fp16 non-mixed precision, fp8 mixed precision -->

#### Speeds, Sizes, Times [optional]

<!-- This section provides information about throughput, start/end time, checkpoint size if relevant, etc. -->

[More Information Needed]

## Evaluation

<!-- This section describes the evaluation protocols and provides the results. -->

### Testing Data, Factors & Metrics

#### Testing Data

<!-- This should link to a Dataset Card if possible. -->

[More Information Needed]

#### Factors

<!-- These are the things the evaluation is disaggregating by, e.g., subpopulations or domains. -->

[More Information Needed]

#### Metrics

<!-- These are the evaluation metrics being used, ideally with a description of why. -->

[More Information Needed]

### Results

[More Information Needed]

#### Summary



## Model Examination [optional]

<!-- Relevant interpretability work for the model goes here -->

[More Information Needed]

## Environmental Impact

<!-- Total emissions (in grams of CO2eq) and additional considerations, such as electricity usage, go here. Edit the suggested text below accordingly -->
>>>>>>> origin/main

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
- [C# API reference](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel?view=semantic-kernel-dotnet)
- [Python API reference](https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel-python)
- Java API reference (coming soon)
## Visual Studio Code extension: design semantic functions with ease
The Semantic Kernel extension for Visual Studio Code makes it easy to design and test semantic functions. The extension provides an interface for designing semantic functions and allows you to test them with the push of a button with your existing models and data.
>>>>>>>+Updated upstrea
>>> Stashed changes

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

1. Go to the Quick start page [here](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-csharp) and follow the steps to dive in.
2. You'll need to ensure that you toggle to C# in the the Choose a programming language table at the top of the page.
 ![csharpmap](https://learn.microsoft.com/en-us/semantic-kernel/media/pythonmap.png)

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
- Python API reference (coming soon)
- Java API reference (coming soon)
<<<<<<< Upda
## Visual Studio Code extension: design semantic functions with ease

The Semantic Kernel extension for Visual Studio Code makes it easy to design and test semantic functions. The extension provides an interface for designing semantic functions and allows you to test them with the push of a button with your existing models and data.
<<<<<<< main
The [Semantic Kernel extension for Visual Studio Code](https://learn.microsoft.com/en-us/semantic-kernel/vs-code-tools/)
makes it easy to design and test semantic functions. The extension provides an interface for
designing semantic functions and allows you to test them with a push of a button with your
existing models and data.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
- **Hardware Type:** [More Information Needed]
- **Hours used:** [More Information Needed]
- **Cloud Provider:** [More Information Needed]
- **Compute Region:** [More Information Needed]
- **Carbon Emitted:** [More Information Needed]

## Technical Specifications [optional]

### Model Architecture and Objective

[More Information Needed]

### Compute Infrastructure

[More Information Needed]

#### Hardware
>>>>>>> origin/main

[More Information Needed]

#### Software

[More Information Needed]

<<<<<<< head
## Check out our other repos
=======
## Citation [optional]
>>>>>>> origin/main

<!-- If there is a paper or blog post introducing the model, the APA and Bibtex information for that should go in this section. -->

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
- **Hardware Type:** [More Information Needed]
- **Hours used:** [More Information Needed]
- **Cloud Provider:** [More Information Needed]
- **Compute Region:** [More Information Needed]
- **Carbon Emitted:** [More Information Needed]

## Technical Specifications [optional]

### Model Architecture and Objective

[More Information Needed]

### Compute Infrastructure

[More Information Needed]

#### Hardware
>>>>>>> origin/main

[More Information Needed]

#### Software

[More Information Needed]

<<<<<<< main
## Check out our other repos
=======
## Citation [optional]
>>>>>>> origin/main

<!-- If there is a paper or blog post introducing the model, the APA and Bibtex information for that should go in this section. -->

<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
| Repo                                                                              | Description                                                                                   |
| --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [Chat Copilot](https://github.com/microsoft/chat-copilot)                         | A reference application that demonstrates how to build a chatbot with Semantic Kernel.        |
| [Semantic Kernel Docs](https://github.com/MicrosoftDocs/semantic-kernel-docs)     | The home for Semantic Kernel documentation that appears on the Microsoft learn site.          |
| [Semantic Kernel Starters](https://github.com/microsoft/semantic-kernel-starters) | Starter projects for Semantic Kernel to make it easier to get started.                        |
| [Kernel Memory](https://github.com/microsoft/kernel-memory)                       | A scalable Memory service to store information and ask questions using the RAG pattern.       |
>>> Stashed changes
>>>>>>> origin/PR

## Join the community
# Semantic Kernel

[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)

> ℹ️ **NOTE**: The Python SDK for Semantic Kernel is currently in preview. While most
> of the features available in the C# SDK have been ported, there may be bugs and
> we're working on some features still - these will come into the repo soon. We are
> also actively working on improving the code quality and developer experience,
> and we appreciate your support, input and PRs!

> ℹ️ **NOTE**: This project is in early alpha and, just like AI, will evolve quickly.
> We invite you to join us in developing the Semantic Kernel together!
> Please contribute by
> using GitHub [Discussions](https://github.com/microsoft/semantic-kernel/discussions),
> opening GitHub [Issues](https://github.com/microsoft/semantic-kernel/issues/new/choose),
> sending us [PRs](https://github.com/microsoft/semantic-kernel/pulls).

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

## Get Started with Semantic Kernel ⚡

Here is a quick example of how to use Semantic Kernel from a Python script.

1. Clone the repo and install SK dependencies, e.g. using `pip install -r python/requirements.txt`
2. Create a new Python file and add the code below.
3. Copy and paste your OpenAI **API key** in the script
   (support for Azure OpenAI is work in progress).
4. Using Python 3.8 or later, run the code. Enjoy!

```python
import sys
sys.path.append("./python")  # nopep8
import semantic_kernel as sk
import asyncio


kernel = sk.create_kernel()

kernel.config.add_openai_completion_backend(
    "davinci",
    "text-davinci-003",
    "...OpenAI Key...")

sk_prompt = """
{{$input}}

Give me the TLDR in 5 words.
"""

tldr_function = sk.extensions.create_semantic_function(
    kernel,
    sk_prompt,
    max_tokens=200,
    temperature=0,
    top_p=0.5)

text_to_summarize = """
    1) A robot may not injure a human being or, through inaction,
    allow a human being to come to harm.

    2) A robot must obey orders given it by human beings except where
    such orders would conflict with the First Law.

    3) A robot must protect its own existence as long as such protection
    does not conflict with the First or Second Law.
"""

summary = asyncio.run(kernel.run_on_str_async(text_to_summarize, tldr_function))

print(f"Output: {summary}")

# Output: Robots must not harm humans.
```

## How does this compare to the main C# branch?

Refer to the [FEATURE_PARITY.md](python/FEATURE_PARITY.md) doc to see where
things stand in matching the features and functionality of the main SK branch.

## Contributing and Community
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
**BibTeX:**

[More Information Needed]
>>>>>>> origin/main

**APA:**

[More Information Needed]

## Glossary [optional]

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
**BibTeX:**

[More Information Needed]
>>>>>>> origin/main

**APA:**

[More Information Needed]

## Glossary [optional]

<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
- Read the [documentation](https://aka.ms/sk/learn)
- Learn how to [contribute](https://learn.microsoft.com/en-us/semantic-kernel/get-started/contributing) to the project
- Ask questions in the [GitHub discussions](https://github.com/microsoft/semantic-kernel/discussions)
- Ask questions in the [Discord community](https://aka.ms/SKDiscord)

- Attend [regular office hours and SK community events](COMMUNITY.md)
- Follow the team on our [blog](https://aka.ms/sk/blog)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<!-- If relevant, include terms and calculations in this section that can help readers understand the model or model card. -->
>>>>>>> origin/main

[More Information Needed]

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<!-- If relevant, include terms and calculations in this section that can help readers understand the model or model card. -->
>>>>>>> origin/main

[More Information Needed]

<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
[![semantic-kernel contributors](https://contrib.rocks/image?repo=microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/graphs/contributors)
-   Read the [documentation](https://aka.ms/sk/learn)
-   Learn how to [contribute](https://github.com/microsoft/semantic-kernel/blob/main/CONTRIBUTING.md) to the project
-   Join the [Discord community](https://aka.ms/SKDiscord)
-   Hear from the team on our [blog](https://aka.ms/sk/blog)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
## More Information [optional]
>>>>>>> origin/main

[More Information Needed]

## Model Card Authors [optional]

[More Information Needed]

## Model Card Contact

<<<<<<< head
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
## More Information [optional]
>>>>>>> origin/main

[More Information Needed]

## Model Card Authors [optional]

[More Information Needed]

## Model Card Contact

<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
Licensed under the [MIT](LICENSE) license.
=======
title: SK Api
emoji: 🚀
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
app_port: 3000
suggested_hardware: a10g-small
license: other
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> main
=======
---
license: mit
---
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
[More Information Needed]
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
[More Information Needed]
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
[More Information Needed]
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
[More Information Needed]
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
[More Information Needed]
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
[More Information Needed]
>>>>>>> origin/main
