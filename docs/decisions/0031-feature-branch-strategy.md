---
# Strategy for Community Driven Connectors and Features

status: approved
contact: rogerbarreto
date: 2024-01-24
deciders: rogerbarreto, markwallace-microsoft, dmytrostruk, sergeymenshik
consulted:
informed:
---

# Strategy for Community Driven Connectors and Features

## Context and Problem Statement

Normally Connectors are Middle to Complex new Features that can be developed by a single person or a team. In order to avoid conflicts and to have a better control of the development process, we strongly suggest the usage of a Feature Branch Strategy in our repositories.

In our current software development process, managing changes in the main branch has become increasingly complex, leading to potential conflicts and delays in release cycles.

## Standards and Guidelines Principles

- **Pattern**: The Feature Branch Strategy is a well-known pattern for managing changes in a codebase. It is widely used in the industry and is supported by most version control systems, including GitHub, this also gives further clear picture on how the community can meaningfully contribute to the development of connectors or any other bigger feature for SK.
- **Isolated Development Environments**: By using feature branches, each developer can work on different aspects of the project without interfering with others' work. This isolation reduces conflicts and ensures that the main branch remains stable.
- **Streamlined Integration**: Feature branches simplify the process of integrating new code into the main branch. By dealing with smaller, more manageable changes, the risk of major conflicts during integration is minimized.
- **Efficiency in Code Review**: Smaller, more focused changes in feature branches lead to quicker and more efficient code reviews. This efficiency is not just about the ease of reviewing less code at a time but also about the time saved in understanding the context and impact of the changes.
- **Reduced Risk of Bugs**: Isolating development in feature branches reduces the likelihood of introducing bugs into the main branch. It's easier to identify and fix issues within the confined context of a single feature.
- **Timely Feature Integration**: Small, incremental pull requests allow for quicker reviews and faster integration of features into the feature branch and make it easier to merge down into main as the code was already previously reviewed. This timeliness ensures that features are merged and ready for deployment sooner, improving the responsiveness to changes.
- **Code Testing, Coverage and Quality**: To keep a good code quality is imperative that any new code or feature introduced to the codebase is properly tested and validated. Any new feature or code should be covered by unit tests and integration tests. The code should also be validated by our CI/CD pipeline and follow our code quality standards and guidelines.
- **Examples**: Any new feature or code should be accompanied by examples that demonstrate how to use the new feature or code. This is important to ensure that the new feature or code is properly documented and that the community can easily understand and use it.

### Community Feature Branch Strategy

As soon we identify that contributors are willing to take/create a Feature Issue as a potential connector implementation, we will create a new branch for that feature.

Once we have agreed to take a new connector we will work with the contributors to make sure the implementation progresses and is supported if needed.

The contributor(s) will then be one of the responsibles to incrementally add the majority of changes through small Pull Requests to the feature branch under our supervision and review process.

This strategy involves creating a separate branch in the repository for each new big feature, like connectors. This isolation means that changes are made in a controlled environment without affecting the main branch.

We may also engage in the development and changes to the feature branch when needed, the changes and full or co-authorship on the PRs will be tracked and properly referred into the Release Notes.

#### Pros and Cons

- Good, because it allows for focused development on one feature at a time.
- Good, because it promotes smaller, incremental Pull Requests (PRs), simplifying review processes.
- Good, because it reduces the risk of major bugs being merged into the main branch.
- Good, because it makes the process of integrating features into the main branch easier and faster.
- Bad, potentially, if not managed properly, as it can lead to outdated branches if not regularly synchronized with the main branch.

## Local Deployment Platforms / Offline

### LM Studio

LM Studio has a local deployment option, which can be used to deploy models locally. This option is available for Windows, Linux, and MacOS.

Pros:

- API is very similar to OpenAI API
- Many models are already supported
- Easy to use
- Easy to deploy
- GPU support

Cons:

- May require a license to use in a work environment

### Ollama

Ollama has a local deployment option, which can be used to deploy models locally. This option is available for Linux and MacOS only for now.

Pros:

- Easy to use
- Easy to deploy
- Supports Docker deployment
- GPU support

Cons:

- API is not similar to OpenAI API (Needs a dedicated connector)
- Dont have Windows support

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
| Mistral Support | Yes    | Yes       |

## Connector/Model Priorities

Currently we are looking for community support on the following models

The support on the below can be either achieved creating a practical example using one of the existing Connectors against one of this models or providing a new Connector that supports a deployment platform that hosts one of the models below:

| Model Name | Local Support | Deployment                             | Connectors                                             |
| ---------- | ------------- | -------------------------------------- | ------------------------------------------------------ |
| Gpt-4      | No            | OpenAI, Azure                          | Azure+OpenAI                                           |
| Phi-2      | Yes           | Azure, Hugging Face, LM Studio, Ollama | OpenAI, HuggingFace, LM Studio\*\*\*, Ollama\*\*       |
| Gemini     | No            | Google AI Platform                     | GoogleAI\*\*                                           |
| Llama-2    | Yes           | Azure, LM Studio, HuggingFace, Ollama  | HuggingFace, Azure+OpenAI, LM Studio\*\*\*, Ollama\*\* |
| Mistral    | Yes           | Azure, LM Studio, HuggingFace, Ollama  | HuggingFace, Azure+OpenAI, LM Studio\*\*\*, Ollama\*\* |
| Claude     | No            | Anthropic, Amazon Bedrock              | Anthropic**, Amazon**                                  |
| Titan      | No            | Amazon Bedrock                         | Amazon\*\*                                             |

_\*\* Connectors not yet available_

_\*\*\* May not be needed as an OpenAI Connector can be used_

Connectors may be needed not per Model basis but rather per deployment platform.
For example, using OpenAI or HuggingFace connector you may be able to call a Phi-2 Model.

## Expected Connectors to be implemented

The following deployment platforms are not yet supported by any Connectors and we strongly encourage the community to engage and support on those:

Currently the priorities are ordered but not necessarily needs to be implemented sequentially, an

| Deployment Platform | Local Model Support |
| ------------------- | ------------------- |
| Ollama              | Yes                 |
| GoogleAI            | No                  |
| Anthropic           | No                  |
| Amazon              | No                  |

## Decision Outcome

Chosen option: "Feature Branch Strategy", because it allows individual features to be developed in isolation, minimizing conflicts with the main branch and facilitating easier code reviews.

## Fequent Asked Questions

### Is there a migration strategy for initiatives that followed the old contribution way with forks, and now have to switch to branches in microsoft/semantic-kernel?

You proceed normally with the fork and PR targeting `main`, as soon we identify that your contribution PR to main is a big and desirable feature (Look at the ones we described as expected in this ADR) we will create a dedicated feature branch (`feature-yourfeature`) where you can retarget our forks PR to target it.
All further incremental changes and contributions will follow as normal, but instead of `main` you will be targeting the `feature-*` branch.

### How do you want to solve the "up to date with main branch" problem?

This will happen when we all agreed that the current feature implementation is complete and ready to merge in `main`.

As soon the feature is finished, a merge from main will be pushed into the feature branch.
This will normally trigger the conflicts that need to be sorted.
That normally will be the last PR targeting the feature branch which will be followed right away by another PR from the `feature` branch targeting `main` with minimal conflicts if any.
The merging to main might be fast (as all the intermediate feature PRs were all agreed and approved before)

### Merging main branch to feature branch before finish feature

The merging of the main branch into the feature branch should only be done with the command:

`git checkout <feature branch> && git merge main` without --squash

Merge from the main should never be done by PR to feature branch, it will cause merging history of main merge with history of PR (because PR are merged with --squash), and as a consequence it will generate strange conflicts on subsequent merges of main and also make it difficult to analyze history of feature branch.
