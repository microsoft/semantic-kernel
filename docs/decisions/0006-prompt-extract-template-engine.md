---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-08-25
deciders: shawncal
consulted: 
informed: 
---
# Extract the Prompt Template Engine from Semantic Kernel core

## Context and Problem Statement

The Semantic Kernel includes a default prompt template engine which is used to render Semantic Kernel prompts i.e., `skprompt.txt` files. The prompt template is rendered before being send to the AI to allow the prompt to be generated dynamically e.g., include input parameters or the result of a native or semantic function execution.
To reduce the complexity and API surface of the Semantic Kernel the prompt template engine is going to be extracted and added to it's own package.

The long term goal is to enable the following scenarios:

1. Implement a custom template engine e.g., using Handlebars templates. This is supported now but we want to simplify the API to be implemented.
2. Support using zero or many template engines.

## Decision Drivers

* Reduce API surface and complexity of the Semantic Kernel core.
* Simplify the `IPromptTemplateEngine` interface to make it easier to implement a custom template engine.
* Make the change without breaking existing clients.

## Decision Outcome

* Create a new package called `Microsoft.SemanticKernel.TemplateEngine`.
* Maintain the existing namespace for all prompt template engine code.
* Simplify the `IPromptTemplateEngine` interface to just require implementation of `RenderAsync`.
* Dynamically load the existing `PromptTemplateEngine` if the `Microsoft.SemanticKernel.TemplateEngine` assembly is available.
