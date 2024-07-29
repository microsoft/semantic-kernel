---
status: proposed
contact: afshinm
date: 2024-07-29
deciders: markwallace-microsoft, rogerbarreto, westey-m, afshinm
---

# TypeScript Project Structure

This document proposes a folder structure for the TypeScript implementation of Semantic Kernel.

## Context and Problem Statement

- Provide the folder structure for the TypeScript version of Semantic Kernel
- Design the TypeScript folder structure to be similar (but not exactly the same) to the existing dotnet, Java and Python implementations

## Decision Drivers

- Propose a consistent and idiomatic project structure for the TypeScript implementation of Semantic Kernel
- The SK for TypeScript and dotnet should feel like a single product developed by a single team
- Non-goal: Define the tooling, build pipelines or CI/CD processes for the build and release of SK for TypeScript (This will be a separate ADR)
- Non-goal: Focus on the implementation details for the TypeScript version

## Considered Options

Below is a snapshot of the dotnet folder structure:

```bash
dotnet/src
           Agents
           Connectors
           Experimental
           Extensions
           Functions
           IntegrationTests
           InternalUtilities
           Planners
           Plugins
           SemanticKernel.Abstractions
           SemanticKernel.Core
           SemanticKernel.MetaPackage
           SemanticKernel.UnitTests
```

| Folder                         | Description |
|--------------------------------|-------------|
| Agents                         | Parent folder for various Skills implementations e.g., Core, MS Graph, GRPC, OpenAI, ... |
| Connectors                     | Parent folder for various Connector implementations e.g., AI or Memory services |
| Experimental                   | Parent folder mainly used for experimentation/unstable API (need to confirm) |
| Extensions                     | Parent folder for SK extensions e.g., planner implementations |
| Functions                      | Parent folder for SK functions |
| IntegrationTests               | Integration tests |
| InternalUtilities              | Internal utilities i.e., shared code |
| Planners                       | Parent folder for SK Planners |
| Plugins                        | Parent folder for SK Plugins |
| SemanticKernel.Abstractions    | SK API definitions |
| SemanticKernel.Core            | SK implementation |
| SemanticKernel.MetaPackage     | SK common package collection |
| SemanticKernel.UnitTests       | Unit tests |


And here is the folder structure of the Python SDK:

```bash
python/semantic_kernel
                        agents
                        connectors
                        contents
                        core_plugins
                        exceptions
                        filters
                        functions
                        memory
                        planner
                        prompt_template
                        reliability
                        schema
                        services
                        template_engine
                        text
                        utils
```

| Folder                         | Description |
|--------------------------------|-------------|
| agents                         | Parent folder for various Skills implementations e.g., Core, MS Graph, GRPC, OpenAI, ... |
| connectors                     | Parent folder for various Connector implementations e.g., AI or Memory services |
| contents                       | Utility functions (need to confirm) |
| core_plugins                   | Parent folder for SK Plugins |
| exceptions                     | Parent folder for custom exceptions |
| filters                        | Parent folder for SK Filters (need to confirm) |
| functions                      | Parent folder for SK functions |
| memory                         | Parent folder for various memory implementations e.g., Semantic Text Memory |
| planner                        | Parent folder for SK Planners |
| prompt_template                | Parent folder for Prompt Template parsers e.g., Handlebars prompt template |
| reliability                    | Utilities for reliable service calls e.g., retries |
| schema                         | Kernel Json Schema builder | 
| services                       | Utilities for select an AI provider |
| template_engine                | Prompt Template Engine |
| text                           | Utilities for working with text |
| utils                          | Parent folder for utilities e.g., logging, validation, etc.


Some observations:

1. The dotnet SDK provides a better separation of concerns by classifying each functionality of the app (e.g. Planners) in their own folders (vertical slicing). Example: `dotnet/src/Planners/Planners.OpenAI/Utils`
2. The Python SDK has a mix of vertical and horizontal slicing of the project
3. The dotnet and Python SDKs dedicate a separate folder for all the unit and integration tests (e.g. `dotnet/src/SemanticKernel.UnitTests/Filters/FilterBaseTest.cs`)
4. The folder structure of both the dotnet and Python SDKs are somewhat similar to each other


### Option 1: Vertical slices with tests embedded into each slice

```text
.
└── typescript/
    ├── .vscode
    ├── samples/
    ├── src/
    │   ├── agents/
    │   │   ├── core
    │   │   └── openAI
    │   ├── connectors/
    │   │   ├── AI/
    │   │   │   ├── openAI/
    │   │   │   │   ├── services/
    │   │   │   │   │   ├── openAI.ts
    │   │   │   │   │   └── openAI.test.ts
    │   │   │   │   └── index.ts
    │   │   │   ├── huggingFace/
    │   │   │   │   ├── services/
    │   │   │   │   │   ├── huggingFace.ts
    │   │   │   │   │   └── huggingFace.test.ts
    │   │   │   │   └── index.ts
    │   │   │   └── ...
    │   │   └── memory/
    │   │       ├── azureCongnitiveSearch
    │   │       └── ...
    │   ├── core/
    │   │   ├── kernel.ts
    │   │   ├── kernel.test.ts
    │   │   ├── ...
    │   │   └── index.ts
    │   ├── extensions/
    │   │   ├── handlebars/
    │   │   │   ├── handlebarsPromptTemplate.ts
    │   │   │   ├── handlebarsPromptTemplate.test.ts
    │   │   │   └── index.ts
    │   │   └── liquid/
    │   ├── functions/
    │   │   ├── markdown/
    │   │   ├── prompty/
    │   │   └── ...
    │   ├── planners/
    │   │   ├── handlebars/
    │   │   ├── openAI
    │   │   └── ...
    │   └── plugins/
    │       ├── document
    │       ├── memory
    │       └── MSGraph
    ├── index.ts
    ├── tsconfig.js
    ├── package.json
    └── README.md
```

**_Notes:_**

- This folder structure is based on vertical slices which brings modularity and adaptability.
- Each parent folder represents vertical slice or a feature of Semantic Kernel (e.g. Planners) as opposed to horizontal slices where each parent folder represents a functions (e.g. unit tests, services, utils).
- There is no dedicated tests folder. Test files are co-located next to their implementations which makes them easier to find and locate in the project.
- Each component exposes its public APIs using the `index.ts` file and other files should only depend on the component, instead of its internal implementations (e.g. `import { openAI } from "connectors/ai/openAI";`)


### Option 2: Vertical slices with a separate tests folder

This open is very similar to Option 1 but the main difference is that tests are not in the `src/` folder and there is a dedicated `tests/` parent folder:


```
.
└── typescript/
    ├── .vscode
    ├── samples/
    ├── src/
    │   ├── agents/
    │   │   ├── core
    │   │   └── openAI
    │   ├── connectors/
    │   │   ├── AI/
    │   │   │   ├── openAI/
    │   │   │   │   ├── services/
    │   │   │   │   │   └── openAI.ts
    │   │   │   │   └── index.ts
    │   │   │   ├── huggingFace/
    │   │   │   │   ├── services/
    │   │   │   │   │   └── huggingFace.ts
    │   │   │   │   └── index.ts
    │   │   │   └── ...
    │   │   └── memory/
    │   │       ├── azureCongnitiveSearch
    │   │       └── ...
    │   ├── core/
    │   │   ├── kernel.ts
    │   │   ├── ...
    │   │   └── index.ts
    │   ├── extensions/
    │   │   ├── handlebars/
    │   │   │   ├── handlebarsPromptTemplate.ts
    │   │   │   └── index.ts
    │   │   └── liquid/
    │   ├── functions/
    │   │   ├── markdown/
    │   │   ├── prompty/
    │   │   └── ...
    │   ├── planners/
    │   │   ├── handlebars/
    │   │   ├── openAI
    │   │   └── ...
    │   └── plugins/
    │       ├── document
    │       ├── memory
    │       └── MSGraph
    ├── tests/
    │   ├── agents/
    │   │   └── ...
    │   ├── connectors/
    │   │   └── AI/
    │   │       └── openAI/
    │   │           └── services/
    │   │               └── openAI.test.ts
    │   ├── core/
    │   │   └── ...
    │   └── extensions/
    │       ├── handlebars/
    │       │   └── handlebarsPromptTemplate.test.ts
    │       └── ...
    ├── index.ts
    ├── tsconfig.js
    ├── package.json
    └── README.md
```

## Decision Outcome

TBD