---
# Reestructure of How Sample Code will be Structured In the Repository

status: accepted
contact: rogerbarreto
date: 2024-04-18
deciders: rogerbarreto, markwallace-microsoft, sophialagerkranspandey, matthewbolanos
consulted: dmytrostruk, sergeymenshik, westey-m, eavanvalkenburg
informed:
---

## Context and Problem Statement

- The current way the samples are structured are not very informative and not easy to be found.
- Numbering in Kernel Syntax Examples lost its meaning.
- Naming of the projects don't sends a clear message what they really are.
- Folders and Solutions have `Examples` suffixes which are not necessary as everything in `samples` is already an `example`.

### Current identified types of samples

| Type              | Description                                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| `Getting started` | A single step-by-step tutorial to get started                                                            |
| `Concepts`        | A concept by feature specific code snippets                                                              |
| `LearnResources`  | Code snippets that are related to online documentation sources like Microsoft Learn, DevBlogs and others |
| `Tutorials`       | More in depth step-by-step tutorials                                                                     |
| `Demos`           | Demostration applications that leverage the usage of one or many features                                |

## Decision Drivers and Principles

- **Easy to Search**: Well organized structure, making easy to find the different types of samples
- **Lean namings**: Folder, Solution and Example names are as clear and as short as possible
- **Sends a Clear Message**: Avoidance of Semantic Kernel specific therms or jargons
- **Cross Language**: The sample structure will be similar on all supported SK languages.

## Strategy on the current existing folders

| Current Folder                       | Proposal                                                                  |
| ------------------------------------ | ------------------------------------------------------------------------- |
| KernelSyntaxExamples/Getting_Started | Move into `Getting Started`                                               |
| KernelSyntaxExamples/`Examples??_*`  | Decompose into `Concepts` on multiple conceptual subfolders               |
| AgentSyntaxExamples                  | Decompose into `Concepts` on `Agents` specific subfolders.                |
| DocumentationExamples                | Move into `LearnResources` subfolder and rename to `MicrosoftLearn`       |
| CreateChatGptPlugin                  | Move into `Demo` subfolder                                                |
| HomeAutomation                       | Move into `Demo` subfolder                                                |
| TelemetryExample                     | Move into `Demo` subfolder and rename to `TelemetryWithAppInsights`       |
| HuggingFaceImageTextExample          | Move into `Demo` subfolder and rename to `HuggingFaceImageToText`         |

## Considered Root Structure Options

The following options below are the potential considered options for the root structure of the `samples` folder.

### Option 1 - Ultra Narrow Root Categorization

This option squeezes as much as possible the root of `samples` folder in different subcategories to be minimalist when looking for the samples.

Proposed root structure

```
samples/
├── Tutorials/
│   └── Getting Started/
├── Concepts/
│   ├── Kernel Syntax**
│   └── Agents Syntax**
├── Resources/
└── Demos/
```

Pros:

- Simpler and Less verbose structure (Worse is Better: Less is more approach 😅)
- Begginers will be presented (sibling folders) to other tutorials that may fit better on their need and use case.
- Getting started will not be imposed.

Cons:

- May add extra cognitive load to know that `Getting Started` is a tutorial

### Option 2 - Getting Started Root Categorization

This option brings `Getting Started` to the root `samples` folder compared the structure proposed in `Option 1`.

Proposed root structure

```
samples/
├── Getting Started/
├── Tutorials/
├── Concepts/
│   ├── Kernel Syntax Decomposition**
│   └── Agents Syntax Decomposition**
├── Resources/
└── Demos/
```

Pros:

- Getting Started is the first thing the customer will see
- Beginners will need an extra click to get started.

Cons:

- If the Getting starded example does not have a valid example for the customer it has go back on other folders for more content.

### Option 3 - Conservative + Use Cases Based Root Categorization

This option is more conservative and keeps Syntax Examples projects as root options as well as some new folders for Use Cases, Modalities and Kernel Content.

Proposed root structure

```
samples/
|── QuickStart/
|── Tutorials/
├── KernelSyntaxExamples/
├── AgentSyntaxExamples/
├── UseCases/ OR Demos/
├── KernelContent/ OR Modalities/
├── Documentation/ OR Resources/
```

Pros:

- More conservative approach, keeping KernelSyntaxExamples and AgentSyntaxExamples as root folders won't break any existing internet links.
- Use Cases, Modalities and Kernel Content are more specific folders for different types of samples

Cons:

- More verbose structure adds extra friction to find the samples.
- `KernelContent` or `Modalities` is a internal term that may not be clear for the customer
- `Documentation` may be confused a documents only folder, which actually contains code samples used in documentation. (not clear message)
- `Use Cases` may suggest an idea of real world use cases implemented, where in reality those are simple demostrations of a SK feature.

## KernelSyntaxExamples Decomposition Options

Currently Kernel Syntax Examples contains more than 70 numbered examples all side-by-side, where the number has no progress meaning and is not very informative.

The following options are considered for the KernelSyntaxExamples folder decomposition over multiple subfolders based on Kernel `Concepts` and Features that were developed.

Identified Component Oriented Concepts:

- Kernel

  - Builder
  - Functions
    - Arguments
    - MethodFunctions
    - PromptFunctions
    - Types
    - Results
      - Serialization
      - Metadata
      - Strongly typed
    - InlineFunctions
  - Plugins
    - Describe Plugins
    - OpenAI Plugins
    - OpenAPI Plugins
      - API Manifest
    - gRPC Plugins
    - Mutable Plugins
  - AI Services (Examples using Services thru Kernel Invocation)
    - Chat Completion
    - Text Generation
    - Service Selector
  - Hooks
  - Filters
    - Function Filtering
    - Template Rendering Filtering
    - Function Call Filtering (When available)
  - Templates

- AI Services (Examples using Services directly with Single/Multiple + Streaming and Non-Streaming results)

  - ExecutionSettings
  - Chat Completion
    - Local Models
      - Ollama
      - HuggingFace
      - LMStudio
      - LocalAI
    - Gemini
    - OpenAI
    - AzureOpenAI
    - HuggingFace
  - Text Generation
    - Local Models
      - Ollama
      - HuggingFace
    - OpenAI
    - AzureOpenAI
    - HuggingFace
  - Text to Image
    - OpenAI
    - AzureOpenAI
  - Image to Text
    - HuggingFace
  - Text to Audio
    - OpenAI
  - Audio to Text
    - OpenAI
  - Custom
    - DYI
    - OpenAI
      - OpenAI File

- Memory Services

  - Search

    - Semantic Memory
    - Text Memory
    - Azure AI Search

  - Text Embeddings
    - OpenAI
    - HuggingFace

- Telemetry
- Logging
- Dependecy Injection

- HttpClient

  - Resiliency
  - Usage

- Planners

  - Handlerbars

- Authentication

  - Azure AD

- Function Calling

  - Auto Function Calling
  - Manual Function Calling

- Filtering

  - Kernel Hooks
  - Service Selector

- Templates
- Resilience

- Memory

  - Semantic Memory
  - Text Memory Plugin
  - Search

- RAG

  - Inline
  - Function Calling

- Agents

  - Delegation
  - Charts
  - Collaboration
  - Authoring
  - Tools
  - Chat Completion Agent
    (Agent Syntax Examples Goes here without numbering)

- Flow Orchestrator

### KernelSyntaxExamples Decomposition Option 1 - Concept by Components

This options decomposes the Concepts Structured by Kernel Components and Features.

At first is seems logical and easy to understand how the concepts are related and can be evolved into more advanced concepts following the provided structure.

Large (Less files per folder):

```
Concepts/
├── Kernel/
│   ├── Builder/
│   ├── Functions/
│   │   ├── Arguments/
│   │   ├── MethodFunctions/
│   │   ├── PromptFunctions/
│   │   ├── Types/
│   │   ├── Results/
│   │   │   ├── Serialization/
│   │   │   ├── Metadata/
│   │   │   └── Strongly typed/
│   │   └── InlineFunctions/
│   ├── Plugins/
│   │   ├── Describe Plugins/
│   │   ├── OpenAI Plugins/
│   │   ├── OpenAPI Plugins/
│   │   │   └── API Manifest/
│   │   ├── gRPC Plugins/
│   │   └── Mutable Plugins/
│   ├── AI Services (Examples using Services thru Kernel Invocation)/
│   │   ├── Chat Completion/
│   │   ├── Text Generation/
│   │   └── Service Selector/
│   ├── Hooks/
│   ├── Filters/
│   │   ├── Function Filtering/
│   │   ├── Template Rendering Filtering/
│   │   └── Function Call Filtering (When available)/
│   └── Templates/
├── AI Services (Examples using Services directly with Single/Multiple + Streaming and Non-Streaming results)/
│   ├── ExecutionSettings/
│   ├── Chat Completion/
│   │   ├── LocalModels/
|   │   │   ├── LMStudio/
|   │   │   ├── LocalAI/
|   │   │   ├── Ollama/
|   │   │   └── HuggingFace/
│   │   ├── Gemini/
│   │   ├── OpenAI/
│   │   ├── AzureOpenAI/
│   │   ├── LMStudio/
│   │   ├── Ollama/
│   │   └── HuggingFace/
│   ├── Text Generation/
│   │   ├── LocalModels/
|   │   │   ├── Ollama/
|   │   │   └── HuggingFace/
│   │   ├── OpenAI/
│   │   ├── AzureOpenAI/
│   │   └── HuggingFace/
│   ├── Text to Image/
│   │   ├── OpenAI/
│   │   └── AzureOpenAI/
│   ├── Image to Text/
│   │   └── HuggingFace/
│   ├── Text to Audio/
│   │   └── OpenAI/
│   ├── Audio to Text/
│   │   └── OpenAI/
│   └── Custom/
│       ├── DYI/
│       └── OpenAI/
│           └── OpenAI File/
├── Memory Services/
│   ├── Search/
│   │   ├── Semantic Memory/
│   │   ├── Text Memory/
│   │   └── Azure AI Search/
│   └── Text Embeddings/
│       ├── OpenAI/
│       └── HuggingFace/
├── Telemetry/
├── Logging/
├── Dependency Injection/
├── HttpClient/
│   ├── Resiliency/
│   └── Usage/
├── Planners/
│   └── Handlerbars/
├── Authentication/
│   └── Azure AD/
├── Function Calling/
│   ├── Auto Function Calling/
│   └── Manual Function Calling/
├── Filtering/
│   ├── Kernel Hooks/
│   └── Service Selector/
├── Templates/
├── Resilience/
├── Memory/
│   ├── Semantic Memory/
│   ├── Text Memory Plugin/
│   └── Search/
├── RAG/
│   ├── Inline/
│   └── Function Calling/
├── Agents/
│   ├── Delegation/
│   ├── Charts/
│   ├── Collaboration/
│   ├── Authoring/
│   ├── Tools/
│   └── Chat Completion Agent/
│       (Agent Syntax Examples Goes here without numbering)
└── Flow Orchestrator/
```

Compact (More files per folder):

```
Concepts/
├── Kernel/
│   ├── Builder/
│   ├── Functions/
│   ├── Plugins/
│   ├── AI Services (Examples using Services thru Kernel Invocation)/
│   │   ├── Chat Completion/
│   │   ├── Text Generation/
│   │   └── Service Selector/
│   ├── Hooks/
│   ├── Filters/
│   └── Templates/
├── AI Services (Examples using Services directly with Single/Multiple + Streaming and Non-Streaming results)/
│   ├── Chat Completion/
│   ├── Text Generation/
│   ├── Text to Image/
│   ├── Image to Text/
│   ├── Text to Audio/
│   ├── Audio to Text/
│   └── Custom/
├── Memory Services/
│   ├── Search/
│   └── Text Embeddings/
├── Telemetry/
├── Logging/
├── Dependency Injection/
├── HttpClient/
│   ├── Resiliency/
│   └── Usage/
├── Planners/
│   └── Handlerbars/
├── Authentication/
│   └── Azure AD/
├── Function Calling/
│   ├── Auto Function Calling/
│   └── Manual Function Calling/
├── Filtering/
│   ├── Kernel Hooks/
│   └── Service Selector/
├── Templates/
├── Resilience/
├── RAG/
├── Agents/
└── Flow Orchestrator/
```

Pros:

- Easy to understand how the components are related
- Easy to evolve into more advanced concepts
- Clear picture where to put or add more samples for a specific feature

Cons:

- Very deep structure that may be overwhelming for the developer to navigate
- Although the structure is clear, it may be too verbose

### KernelSyntaxExamples Decomposition Option 2 - Concept by Components Flattened Version

Similar approach to Option 1, but with a flattened structure using a single level of folders to avoid deep nesting and complexity authough keeping easy to navigate around the componentized concepts.

Large (Less files per folder):

```
Concepts/
├── KernelBuilder
├── Kernel.Functions.Arguments
├── Kernel.Functions.MethodFunctions
├── Kernel.Functions.PromptFunctions
├── Kernel.Functions.Types
├── Kernel.Functions.Results.Serialization
├── Kernel.Functions.Results.Metadata
├── Kernel.Functions.Results.StronglyTyped
├── Kernel.Functions.InlineFunctions
├── Kernel.Plugins.DescribePlugins
├── Kernel.Plugins.OpenAIPlugins
├── Kernel.Plugins.OpenAPIPlugins.APIManifest
├── Kernel.Plugins.gRPCPlugins
├── Kernel.Plugins.MutablePlugins
├── Kernel.AIServices.ChatCompletion
├── Kernel.AIServices.TextGeneration
├── Kernel.AIServices.ServiceSelector
├── Kernel.Hooks
├── Kernel.Filters.FunctionFiltering
├── Kernel.Filters.TemplateRenderingFiltering
├── Kernel.Filters.FunctionCallFiltering
├── Kernel.Templates
├── AIServices.ExecutionSettings
├── AIServices.ChatCompletion.Gemini
├── AIServices.ChatCompletion.OpenAI
├── AIServices.ChatCompletion.AzureOpenAI
├── AIServices.ChatCompletion.HuggingFace
├── AIServices.TextGeneration.OpenAI
├── AIServices.TextGeneration.AzureOpenAI
├── AIServices.TextGeneration.HuggingFace
├── AIServices.TextToImage.OpenAI
├── AIServices.TextToImage.AzureOpenAI
├── AIServices.ImageToText.HuggingFace
├── AIServices.TextToAudio.OpenAI
├── AIServices.AudioToText.OpenAI
├── AIServices.Custom.DIY
├── AIServices.Custom.OpenAI.OpenAIFile
├── MemoryServices.Search.SemanticMemory
├── MemoryServices.Search.TextMemory
├── MemoryServices.Search.AzureAISearch
├── MemoryServices.TextEmbeddings.OpenAI
├── MemoryServices.TextEmbeddings.HuggingFace
├── Telemetry
├── Logging
├── DependencyInjection
├── HttpClient.Resiliency
├── HttpClient.Usage
├── Planners.Handlerbars
├── Authentication.AzureAD
├── FunctionCalling.AutoFunctionCalling
├── FunctionCalling.ManualFunctionCalling
├── Filtering.KernelHooks
├── Filtering.ServiceSelector
├── Templates
├── Resilience
├── RAG.Inline
├── RAG.FunctionCalling
├── Agents.Delegation
├── Agents.Charts
├── Agents.Collaboration
├── Agents.Authoring
├── Agents.Tools
├── Agents.ChatCompletionAgent
└── FlowOrchestrator
```

Compact (More files per folder):

```
Concepts/
├── KernelBuilder
├── Kernel.Functions
├── Kernel.Plugins
├── Kernel.AIServices
├── Kernel.Hooks
├── Kernel.Filters
├── Kernel.Templates
├── AIServices.ChatCompletion
├── AIServices.TextGeneration
├── AIServices.TextToImage
├── AIServices.ImageToText
├── AIServices.TextToAudio
├── AIServices.AudioToText
├── AIServices.Custom
├── MemoryServices.Search
├── MemoryServices.TextEmbeddings
├── Telemetry
├── Logging
├── DependencyInjection
├── HttpClient
├── Planners.Handlerbars
├── Authentication.AzureAD
├── FunctionCalling
├── Filtering
├── Templates
├── Resilience
├── RAG
├── Agents
└── FlowOrchestrator
```

Pros:

- Easy to understand how the components are related
- Easy to evolve into more advanced concepts
- Clear picture where to put or add more samples for a specific feature
- Flattened structure avoids deep nesting and makes it easier to navigate on IDEs and GitHub UI.

Cons:

- Although the structure easy to navigate, it may be still too verbose

# KernelSyntaxExamples Decomposition Option 3 - Concept by Feature Grouping

This option decomposes the Kernel Syntax Examples by grouping big and related features together.

```
Concepts/
├── Functions/
├── Chat Completion/
├── Text Generation/
├── Text to Image/
├── Image to Text/
├── Text to Audio/
├── Audio to Text/
├── Telemetry
├── Logging
├── Dependecy Injection
├── Plugins
├── Auto Function Calling
├── Filtering
├── Memory
├── Search
├── Agents
├── Templates
├── RAG
├── Prompts
└── LocalModels/
```

Pros:

- Smaller structure, easier to navigate
- Clear picture where to put or add more samples for a specific feature

Cons:

- Don't give a clear picture of how the components are related
- May require more examples per file as the structure is more high level
- Harder to evolve into more advanced concepts
- More examples will be sharing the same folder, making it harder to find a specific example (major pain point for the KernelSyntaxExamples folder)

# KernelSyntaxExamples Decomposition Option 4 - Concept by Difficulty Level

Breaks the examples per difficulty level, from basic to expert. The overall structure would be similar to option 3 although only subitems would be different if they have that complexity level.

```
Concepts/
├── 200-Basic
|  ├── Functions
|  ├── Chat Completion
|  ├── Text Generation
|  └── ..Basic only folders/files ..
├── 300-Intermediate
|  ├── Functions
|  ├── Chat Completion
|  └── ..Intermediate only folders/files ..
├── 400-Advanced
|  ├── Manual Function Calling
|  └── ..Advanced only folders/files ..
├── 500-Expert
|  ├── Functions
|  ├── Manual Function Calling
|  └── ..Expert only folders/files ..

```

Pros:

- Begginers will be oriented to the right difficulty level and examples will be more organized by complexity

Cons:

- We don't have a definition on what is basic, intermediate, advanced and expert levels and difficulty.
- May require more examples per difficulty level
- Not clear how the components are related
- When creating examples will be hard to know what is the difficulty level of the example as well as how to spread multiple examples that may fit in multiple different levels.

## Decision Outcome

Chosen options:

[x] Root Structure Decision: **Option 2** - Getting Started Root Categorization

[x] KernelSyntaxExamples Decomposition Decision: **Option 3** - Concept by Feature Grouping
