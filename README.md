# SK Api

This repository contains the SK Api, a powerful tool designed to facilitate seamless integration and interaction with various services. The API is built to be robust, efficient, and easy to use, providing developers with the necessary tools to build and deploy applications quickly.

## Features

- **High Performance**, capable of handling large volumes of requests with minimal latency.

- **Scalability**: Easily scale your applications to meet growing demands without compromising performance.

- **Security**: Built-in security features to protect your data and ensure safe transactions.

- **Flexibility**: Compatible with various platforms and can be customized to meet specific project requirements.

## Getting Started

To start using the SK Api, follow these steps:

1. **Installation**: Clone the repository and install the necessary dependencies.

   ```bash
   git clone https://github.com/yourusername/sk-api.git
   cd sk-api
   npm install
   ```

2. **Configuration**: Configure the API settings by editing the `config.json` file to match your environment and requirements.

3. **Running the API**: Start the API server using the following command:

   ```bash
   npm start
   ```

4. **Testing**
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

It provides:

#### Please star the repo to show your support for this project

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

<!-- Provide a quick summary of what the model is/does. -->

This modelcard aims to be a base template for new models. It has been generated using [this raw template](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/modelcard_template.md?plain=1).

## Model Details

### Model Description

<!-- Provide a quick summary of what the model is/does. -->

This modelcard aims to be a base template for new models. It has been generated using [this raw template](https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/templates/modelcard_template.md?plain=1).

## Model Details

### Model Description

1. Clone the repository: `git clone https://github.com/microsoft/semantic-kernel.git`
   1. To access the latest Java code, clone and checkout the Java development branch: `git clone -b java-development https://github.com/microsoft/semantic-kernel.git`

2. Follow the instructions [here](https://github.com/microsoft/semantic-kernel/blob/main/java/samples/sample-code/README.md)

## Learning how to use Semantic Kernel
To learn how to use the Semantic Kernel, you can explore various resources and tutorials available in the repository. The Semantic Kernel is a versatile tool designed to facilitate the integration of semantic understanding into applications. It provides a range of functionalities that enable developers to build more intelligent and context-aware systems.                                                                                                                                                      
### Key Features
- **Semantic
<!-- Provide a longer summary of what this model is. -->

- [Getting Started with C# notebook](dotnet/notebooks/00-getting-started.ipynb)
- [Getting Started with Python notebook](python/samples/getting_started/00-getting-started.ipynb)

- [Getting Started with C# notebook](dotnet/notebooks/00-getting-started.ipynb)
- [Getting Started with Python notebook](python/samples/getting_started/00-getting-started.ipynb)

- **Developed by:** [More Information Needed]
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Model type:** [More Information Needed]
- **Language(s) (NLP):** [More Information Needed]
- **License:** [More Information Needed]
- **Finetuned from model [optional]:** [More Information Needed]

1. 📖 [Getting Started](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)
1. 🔌 [Detailed Samples](https://learn.microsoft.com/en-us/semantic-kernel/get-started/detailed-samples)
1. 💡 [Concepts](https://learn.microsoft.com/en-us/semantic-kernel/concepts/agents)

<!-- Provide a longer summary of what this model is. -->

- [Getting Started with C# notebook](dotnet/notebooks/00-getting-started.ipynb)
- [Getting Started with Python notebook](python/samples/getting_started/00-getting-started.ipynb)

- **Developed by:** [More Information Needed]
- **Funded by [optional]:** [More Information Needed]
- **Shared by [optional]:** [More Information Needed]
- **Model type:** [More Information Needed]
- **Language(s) (NLP):** [More Information Needed]
- **License:** [More Information Needed]
- **Finetuned from model [optional]:** [More Information Needed]

1. 📖 [Getting Started](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)
1. 🔌 [Detailed Samples](https://learn.microsoft.com/en-us/semantic-kernel/get-started/detailed-samples)
1. 💡 [Concepts](https://learn.microsoft.com/en-us/semantic-kernel/concepts/agents)
2. 8. 📊 [Integrating with external data sources](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/external-data-integration)                                                                                                                                                      

### Model Sources [optional]

1. 📖 [Overview of the kernel](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/)
2. 🔌 [Understanding AI plugins](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/plugins)
3. 👄 [Creating semantic functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/semantic-functions)
4. 💽 [Creating native functions](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/native-functions)
5. ⛓️ [Chaining functions together](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chaining-functions)
6. 🤖 [Auto create plans with planner](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/planner)
7. 💡 [Create and run a ChatGPT plugin](https://learn.microsoft.com/en-us/semantic-kernel/ai-orchestration/chatgpt-plugins)

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

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

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

Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).

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

## Enhancing Documentation

### Detailed Explanations and Examples

To enhance the existing documentation, we have added more detailed explanations and examples to help users understand how to use the various features of the repository. These explanations and examples are included in the relevant sections of the documentation files such as `README.md` and `java/README.md`.

### Code Snippets and Usage Examples

We have included more code snippets and usage examples in the documentation to provide practical guidance on how to use the repository's features. These code snippets and examples are designed to help users quickly grasp the concepts and apply them in their own projects.

### Repository Structure Explanation

To help users navigate the repository, we have added a section that explains the structure of the repository and the purpose of each directory and file. This section provides an overview of the repository's organization and helps users understand where to find specific components and resources.

## Security Fixes

This repository uses several tools to automatically identify and fix security vulnerabilities:

### CodeQL

CodeQL is used to analyze the code for security vulnerabilities and errors. The results are shown as code scanning alerts in GitHub. The repository includes multiple CodeQL workflows such as `.github/workflows/codeql-adv.yml`, `.github/workflows/codeql-analysis.yml`, and `.github/workflows/codeql.yml`. These workflows are configured to run on push, pull request, and scheduled events. CodeQL analyzes various languages including C/C++, C#, Java, JavaScript, TypeScript, Python, and Ruby.

For more information, see the [CodeQL documentation](https://docs.github.com/en/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/about-code-scanning-with-codeql).

### Dependabot

Dependabot automatically checks for updates to dependencies and creates pull requests to update them. This helps in keeping the dependencies up-to-date and secure, reducing the risk of vulnerabilities in outdated packages. The repository includes a Dependabot configuration file `.github/dependabot.yml`. The configuration includes updates for nuget, npm, pip, and github-actions, and is set to run weekly on Monday.

For more information, see the [Dependabot documentation](https://docs.github.com/en/code-security/supply-chain-security/keeping-your-dependencies-updated-automatically).

### Frogbot

Frogbot uses JFrog Xray to scan the project for security vulnerabilities. It automatically creates pull requests with fixes for vulnerable project dependencies. The repository includes Frogbot workflows such as `.github/workflows/frogbot-scan-and-fix.yml` and `.github/workflows/frogbot-scan-pr.yml`. These workflows are configured to run on push and pull request events, respectively. The necessary environment variables for JFrog Xray and GitHub token are set in the workflows.

For more information, see the [Frogbot documentation](https://github.com/jfrog/frogbot#frogbot).

### Additional Security Linters

To further enhance security, the repository integrates additional security linters:

* **ESLint**: For JavaScript/TypeScript code, ESLint helps identify and report on patterns found in ECMAScript/JavaScript code. The repository includes an ESLint workflow in `.github/workflows/eslint.yml`.
* **Bandit**: For Python code, Bandit is a security linter designed to find common security issues. The repository includes a Bandit workflow in `.github/workflows/bandit.yml`.
* **DevSkim**: A security linter for various languages, DevSkim helps identify potential security issues early in the development process. The repository includes a DevSkim workflow in `.github/workflows/devskim.yml`.
* **PHPMD**: For PHP code, PHPMD is a tool that looks for several potential problems within the source code. The repository includes a PHPMD workflow in `.github/workflows/phpmd.yml`.
* **rust-clippy**: For Rust code, rust-clippy is a tool that runs a bunch of lints to catch common mistakes and help improve Rust code. The repository includes a rust-clippy workflow in `.github/workflows/rust-clippy.yml`.
* **lintr**: For R code, lintr provides static code analysis, checking for adherence to a given style, identifying syntax errors, and possible semantic issues. The repository includes a lintr workflow in `.github/workflows/lintr.yml`.

### Automated Security Testing

The repository is set up with automated security testing workflows to ensure continuous security validation:

* **EthicalCheck**: For API security testing, the repository includes an EthicalCheck workflow in `.github/workflows/ethicalcheck.yml`.
* **Mayhem for API**: For API fuzz testing, the repository includes a Mayhem for API workflow in `.github/workflows/mayhem-for-api.yml`.
* **OSSAR**: For open source static analysis, the repository includes an OSSAR workflow in `.github/workflows/ossar.yml`.

### Security Policies and Best Practices

The repository follows documented security policies and best practices to ensure the security of the project. These include guidelines for secure coding, regular security reviews, and mandatory security training for developers. The process for monitoring and responding to security alerts is also documented.

For more information, see the `SECURITY.md` file in the repository.
