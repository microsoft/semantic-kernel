---
# Implementing Feature Branch Strategy for Community Driven Connectors

status: proposed
contact: rogerbarreto
date: 2024-01-16
deciders: rogerbarreto, markwallace-microsoft, dmytrostruk, sergeymenshik
consulted:
informed:
---

# Implementing Feature Branch Strategy for Community Driven Connectors

## Context and Problem Statement

Normally Connectors are Middle to Complex new Features that can be developed by a single person or a team. In order to avoid conflicts and to have a better control of the development process, we strongly suggest the usage of a Feature Branch Strategy in our repositories.

In our current software development process, managing changes in the main branch has become increasingly complex, leading to potential conflicts and delays in release cycles.

## Decision Drivers

- **Pattern**: The Feature Branch Strategy is a well-known pattern for managing changes in a codebase. It is widely used in the industry and is supported by most version control systems, including GitHub, this also gives further clear picture on how the community can meaningfully contribute to the development of connectors or any other bigger feature for SK.

- **Isolated Development Environments**: By using feature branches, each developer can work on different aspects of the project without interfering with others' work. This isolation reduces conflicts and ensures that the main branch remains stable.
- **Streamlined Integration**: Feature branches simplify the process of integrating new code into the main branch. By dealing with smaller, more manageable changes, the risk of major conflicts during integration is minimized.
- **Efficiency in Code Review**: Smaller, more focused changes in feature branches lead to quicker and more efficient code reviews. This efficiency is not just about the ease of reviewing less code at a time but also about the time saved in understanding the context and impact of the changes.
- **Reduced Risk of Bugs**: Isolating development in feature branches reduces the likelihood of introducing bugs into the main branch. It's easier to identify and fix issues within the confined context of a single feature.
- **Timely Feature Integration**: Small, incremental pull requests allow for quicker reviews and faster integration of features into the feature branch and make it easier to merge down into main as the code was already previously reviewed. This timeliness ensures that features are merged and ready for deployment sooner, improving the responsiveness to changes.

## Considered Options

- Community Feature Branch Strategy

### Community Feature Branch Strategy

As soon we identify that contributors are willing to take/create a Feature Issue as a potential connector implementation, we will create a new branch for that feature.

The contributor(s) will then be one of the responsibles to incrementally add the majority of changes through small Pull Requests to the feature branch under our supervision and review process.

This strategy involves creating a separate branch in the repository for each new big feature, like connectors. This isolation means that changes are made in a controlled environment without affecting the main branch.

We may also engage in the development and changes to the feature branch when needed, the changes and full or co-authorship on the PRs will be tracked and properly referred into the Release Notes.

#### Pros and Cons

- Good, because it allows for focused development on one feature at a time.
- Good, because it promotes smaller, incremental Pull Requests (PRs), simplifying review processes.
- Good, because it reduces the risk of major bugs being merged into the main branch.
- Good, because it makes the process of integrating features into the main branch easier and faster.
- Bad, potentially, if not managed properly, as it can lead to outdated branches if not regularly synchronized with the main branch.

## Validation

The effectiveness of the feature branch strategy will be validated through regular code reviews, successful CI/CD pipeline runs, and feedback from the development team.

## Connector/Model Priorities

Currently we are looking for community support on the following models

The support on the below can be either achieved creating a practical example using one of the existing Connectors against one of this models or providing a new Connector that supports a platform that hosts one of the models below:

| Model Name | Local Support | Deployment                           | Connectors                                    |
| ---------- | ------------- | ------------------------------------ | --------------------------------------------- |
| Gpt-4      | No            | OpenAI, Azure Open AI                | OpenAI                                        |
| Phi-2      | Yes           | Azure OpenAI, Hugging Face, LMStudio | OpenAI, HuggingFace, LMStudio\*\*             |
| Gemini     | No            | Google AI Platform                   | GoogleAI\*\*                                  |
| Llama-2    | Yes           | LMStudio, HuggingFace, Ollama        | HuggingFace, OpenAI, LMStudio\*\*, Ollama\*\* |
| Mistral    | Yes           | LMStudio, HuggingFace, Ollama        | HuggingFace, OpenAI, LMStudio\*\*, Ollama\*\* |
| Claude     | No            | Anthropic, Amazon Bedrock            | Anthropic**, Amazon**                         |
| Titan      | No            | Amazon Bedrock                       | Amazon\*\*                                    |

_\*\* Connectors not yet available_

Connectors may be needed not per Model basis but rather per platform.
For example, using OpenAI or HuggingFace connector you may be able to call a Phi-2 Model.

### Potential deployments for connector support:

- **Local Model Support**
  - LM Studio
  - Ollama
  - Pure C# (e.g. LlamaSharp or ONNX runtime)
- Amazon Bedrock
- Google AI Platform

## Local Deployment / Offline

### LM Studio

LM Studio has a local deployment option, which can be used to deploy models locally. This option is available for Windows, Linux, and MacOS.

Pros: - API is very similar to OpenAI API - Many models are already supported - Easy to use - Easy to deploy - GPU support

### Ollama

Ollama has a local deployment option, which can be used to deploy models locally. This option is available for Linux and MacOS only for now.

Pros: - Easy to use - Easy to deploy - Supports Docker deployment - GPU support
Cons: - API is not similar to OpenAI API (Needs a dedicated connector) - Limited model support (does not support Phi-2) - Dont have Windows support

### Comparison

| Feature               | Ollama                                              | LM Studio                                                                               |
| --------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Local LLM             | Yes                                                 | Yes                                                                                     |
| OpenAI API Similarity | Yes                                                 | Yes                                                                                     |
| Windows Support       | No                                                  | Yes                                                                                     |
| Linux Support         | Yes                                                 | Yes                                                                                     |
| MacOS Support         | Yes                                                 | Yes                                                                                     |
| Number of Models      | [61](https://ollama.ai/library) +Any GGUF converted | [25](https://github.com/lmstudio-ai/model-catalog/tree/main/models) +Any GGUF Converted |

| Model Support   | Ollama | LM Studio |
| --------------- | ------ | --------- |
| Phi-2 Support   | Yes    | Yes       |
| Llama-2 Support | Yes    | Yes       |
| Mixtral Support | Yes    | Yes       |

### Notes

- Is very important to have easy to reproduce examples for any new model support or added feature.
- While implementing new features code follow our current existing code-base as a reference and ensure that the code is validated by our CI/CD pipeline requirements, before submitting a PR for review.

## Decision Outcome

Chosen option: "Feature Branch Strategy", because it allows individual features to be developed in isolation, minimizing conflicts with the main branch and facilitating easier code reviews.
