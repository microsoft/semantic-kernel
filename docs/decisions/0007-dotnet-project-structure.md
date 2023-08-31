---

# These are optional elements. Feel free to remove any of them

status: proposed
date: {YYYY-MM-DD when the decision was last updated}
deciders: {list everyone involved in the decision}
consulted: {list everyone whose opinions are sought (typically subject-matter experts); and with whom there is a two-way communication}
informed: {list everyone who is kept up-to-date on progress; and with whom there is a one-way communication}
---

# DotNet Project Structure for 1.0 Release

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.
 You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

### Current Project Structure

```text
SK-dotnet
├── samples/
└── src/
    ├── connectors/
    │   ├── Connectors.AI.OpenAI*
    │   ├── Connectors...
    │   └── Connectors.UnitTests
    ├── extensions/
    │   ├── Planner.ActionPlanner*
    │   ├── Planner.SequentialPlanner*
    │   ├── Planner.StepwisePlanner
    │   ├── TemplateEngine.PromptTemplateEngine*
    │   └── Extensions.UnitTests
    ├── InternalUtilities/
    ├── skills/
    │   ├── Skills.Core
    │   ├── Skills.Document
    │   ├── Skills.Grpc
    │   ├── Skills.MsGraph
    │   ├── Skills.OpenAPI
    │   ├── Skills.Web
    │   └── Skills.UnitTests
    ├── IntegrationTests
    ├── SemanticKernel*
    ├── SemanticKernel.Abstractions*
    ├── SemanticKernel.MetaPackage
    └── SemanticKernel.UnitTests
```

\\* - Means the project is part of the Semantic Kernel meta package

### Project Descriptions

| Project                             | Description |
|-------------------------------------|-------------|
| Connectors.AI.OpenAI                | Azure OpenAI and OpenAI service connectors |
| Connectors...                       | Collection of other AI service connectors, some of which will move to another repository |
| Connectors.UnitTests                | Connector unit tests |
| Planner.ActionPlanner               | Semantic Kernel implementation of an action planner |
| Planner.SequentialPlanner           | Semantic Kernel implementation of a sequential planner |
| Planner.StepwisePlanner             | Semantic Kernel implementation of a stepwise planner |
| TemplateEngine.PromptTemplateEngine | Prompt template engine implementation which is used by Semantic Functions only |
| Extensions.UnitTests                | Extensions unit tests |
| InternalUtilities                   | Internal utilities which are reused by multiple NuGet packages (all internal)  |
| Skills.Core                         | Core set of native functions which are provided to support Semantic Functions |
| Skills.Document                     | Native functions for interacting with Microsoft documents |
| Skills.Grpc                         | Semantic Kernel integration for GRPC based endpoints |
| Skills.MsGraph                      | Native functions for interacting with Microsoft Graph endpoints |
| Skills.OpenAPI                      | Semantic Kernel integration for OpenAI endpoints and reference Azure Key Vault implementation |
| Skills.Web                          | Native functions for interacting with Web endpoints e.g., Bing, Google, File download |
| Skills.UnitTests                    | Skills unit tests |
| IntegrationTests                    | Semantic Kernel integration tests |
| SemanticKernel                      | Semantic Kernel core implementation |
| SemanticKernel.Abstractions         | Semantic Kernel abstractions i.e., interface, abstract classes, supporting classes, ... |
| SemanticKernel.MetaPackage          | Semantic Kernel meta package i.e., a NuGet package that references other required Semantic Kernel NuGet packages |
| SemanticKernel.UnitTests            | Semantic Kernel unit tests |

### Naming Pattern

Below are some different examples of Assembly and root namespace naming that are used in the projects.

```xml
    <AssemblyName>Microsoft.SemanticKernel.Abstractions</AssemblyName>
    <RootNamespace>Microsoft.SemanticKernel</RootNamespace>

    <AssemblyName>Microsoft.SemanticKernel.Core</AssemblyName>
    <RootNamespace>Microsoft.SemanticKernel</RootNamespace>

    <AssemblyName>Microsoft.SemanticKernel.Planning.ActionPlanner</AssemblyName>
    <RootNamespace>Microsoft.SemanticKernel.Planning.Action</RootNamespace>

    <AssemblyName>Microsoft.SemanticKernel.Skills.Core</AssemblyName>
    <RootNamespace>$(AssemblyName)</RootNamespace>
```

### Current Folder Structure

```text
dotnet/
├── samples/
│   ├── ApplicationInsightsExample/
│   ├── KernelSyntaxExamples/
│   └── NCalcSkills/
└── src/
    ├── Connectors/
    │   ├── Connectors.AI.OpenAI*
    │   ├── Connectors...
    │   └── Connectors.UnitTests
    ├── Extensions/
    │   ├── Planner.ActionPlanner
    │   ├── Planner.SequentialPlanner
    │   ├── Planner.StepwisePlanner
    │   ├── TemplateEngine.PromptTemplateEngine
    │   └── Extensions.UnitTests
    ├── InternalUtilities/
    ├── Skills/
    │   ├── Skills.Core
    │   ├── Skills.Document
    │   ├── Skills.Grpc
    │   ├── Skills.MsGraph
    │   ├── Skills.OpenAPI
    │   ├── Skills.Web

    │   └── Skills.UnitTests
    ├── IntegrationTests/
    ├── SemanticKernel/
    ├── SemanticKerne.Abstractions/
    ├── SemanticKernel.MetaPackage/
    └── SemanticKernel.UnitTests/

```


<!-- This is an optional element. Feel free to remove. -->
## Decision Drivers

* Semantic Kernel core should only contain functionality related to AI orchestration
  * Remove prompt template engine and semantic functions
* Semantic Kernel abstractions should only interfaces, abstract classes and minimal classes to support these
* Avoid having too many assemblies because of impact of signing these and to reduce complexity
* Remove `Skills` naming from NuGet packages
* Have consistent naming for assemblies and their root namespaces

## Considered Options

* Move skills projects to be extensions and merge some packages
* {title of option 2}
* {title of option 3}
* … <!-- numbers of options can vary -->

In all cases the following changes will be made:

* Move non core Connectors to a separate repository
* Merge prompt template engine, core skills and semantic functions into a single package

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

## Pros and Cons of the Options

### Move skills projects to be extensions and merge some packages

```text
SK-dotnet
├── samples/
└── src/
    ├── connectors/
    │   ├── Connectors.AI.OpenAI*
    │   └── Connectors.UnitTests
    ├── extensions/
    │   ├── Extensions.Planner*
    │   ├── Extensions.Prompt*
    │   ├── Extensions.OpenAPI
    │   ├── Extensions.Grpc
    │   ├── Extensions.Web
    │   ├── Extensions.Document
    │   ├── Extensions.MsGraph
    │   └── Extensions.UnitTests
    ├── InternalUtilities/
    ├── IntegrationTests
    ├── SemanticKernel*
    ├── SemanticKernel.Abstractions*
    ├── SemanticKernel.MetaPackage
    └── SemanticKernel.UnitTests

```

### Changes

* Merge all planner related NuGet packages because we want these all in the meta package
* Merge `TemplateEngine.PromptTemplateEngine` and `Skills.Core`. Additionally move all semantic function code to this new package.

### Pros and Cons

* Good, because {argument a}
* Good, because {argument b}

