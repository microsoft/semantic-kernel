---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: markwallace-microsoft
date: 2025-01-17
deciders: markwallace-microsoft, bentho, crickman
consulted: {list everyone whose opinions are sought (typically subject-matter experts); and with whom there is a two-way communication}
informed: {list everyone who is kept up-to-date on progress; and with whom there is a one-way communication}
---

# Schema for Declarative Agent Format

## Context and Problem Statement

This ADR describes a schema which can be used to define an Agent which can be loaded and executed using the Semantic Kernel Agent Framework.

Currently the Agent Framework uses a code first approach to allow Agents to be defined and executed.
Using the schema defined by this ADR developers will be able to declaratively define an Agent and have the Semantic Kernel instantiate and execute the Agent.

Here is some pseudo code to illustrate what we need to be able to do:

```csharp
Kernel kernel = Kernel
    .CreateBuilder()
    .AddAzureAIClientProvider(...)
    .Build();
var text =
    """
    type: azureai_agent
    name: AzureAIAgent
    description: AzureAIAgent Description
    instructions: AzureAIAgent Instructions
    model:
      id: gpt-4o-mini
    tools:
        - name: tool1
          type: code_interpreter
    """;

AzureAIAgentFactory factory = new();
var agent = await KernelAgentYaml.FromAgentYamlAsync(kernel, text, factory);
```

The above code represents the simplest case would work as follows:

1. The `Kernel` instance has the appropriate services e.g. an instance of `AzureAIClientProvider` when creating AzureAI agents.
2. The `KernelAgentYaml.FromAgentYamlAsync` will create one of the built-in Agent instances i.e., one of `ChatCompletionAgent`, `OpenAIAssistantsAgent`, `AzureAIAgent`.
3. The new Agent instance is initialized with it's own `Kernel` instance configured the services and tools it requires and a default initial state.

Note: Consider creating just plain `Agent` instances and extending the `Agent` abstraction to contain a method which allows the Agent instance to be invoked with user input.

```csharp
Kernel kernel = ...
string text = EmbeddedResource.Read("MyAgent.yaml");
AgentFactory agentFactory = new AggregatorAgentFactory(
    new ChatCompletionAgentFactory(),
    new OpenAIAssistantAgentFactory(),
    new AzureAIAgentFactory());
var agent = KernelAgentYaml.FromAgentYamlAsync(kernel, text, factory);;
```

The above example shows how different Agent types are supported.

**Note:**

1. Markdown with YAML front-matter (i.e. Prompty format) will be the primary serialization format used.
2. Providing Agent state is not supported in the Agent Framework at present.
3. We need to decide if the Agent Framework should define an abstraction to allow any Agent to be invoked.
4. We will support JSON also as an out-of-the-box option.

Currently Semantic Kernel supports three Agent types and these have the following properties:

1. [`ChatCompletionAgent`](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.agents.chatcompletionagent?view=semantic-kernel-dotnet):
   - `Arguments`: Optional arguments for the agent. (Inherited from ChatHistoryKernelAgent)
   - `Description`: The description of the agent (optional). (Inherited from Agent)
   - `HistoryReducer`: (Inherited from ChatHistoryKernelAgent)
   - `Id`: The identifier of the agent (optional). (Inherited from Agent)
   - `Instructions`: The instructions of the agent (optional). (Inherited from KernelAgent)
   - `Kernel`: The Kernel containing services, plugins, and filters for use throughout the agent lifetime. (Inherited from KernelAgent)
   - `Logger`: The ILogger associated with this Agent. (Inherited from Agent)
   - `LoggerFactory`: A ILoggerFactory for this Agent. (Inherited from Agent)
   - `Name`: The name of the agent (optional). (Inherited from Agent)
2. [`OpenAIAssistantAgent`](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.agents.agent.description?view=semantic-kernel-dotnet#microsoft-semantickernel-agents-agent-description):
   - `Arguments`: Optional arguments for the agent.
   - `Definition`: The assistant definition.
   - `Description`: The description of the agent (optional). (Inherited from Agent)
   - `Id`: The identifier of the agent (optional). (Inherited from Agent)
   - `Instructions`: The instructions of the agent (optional). (Inherited from KernelAgent)
   - `IsDeleted`: Set when the assistant has been deleted via DeleteAsync(CancellationToken). An assistant removed by other means will result in an exception when invoked.
   - `Kernel`: The Kernel containing services, plugins, and filters for use throughout the agent lifetime. (Inherited from KernelAgent)
   - `Logger`: The ILogger associated with this Agent. (Inherited from Agent)
   - `LoggerFactory`: A ILoggerFactory for this Agent. (Inherited from Agent)
   - `Name`: The name of the agent (optional). (Inherited from Agent)
   - `PollingOptions`: Defines polling behavior
3. [`AzureAIAgent`](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Agents/AzureAI/AzureAIAgent.cs)
   - `Definition`: The assistant definition.
   - `PollingOptions`: Defines polling behavior for run processing.
   - `Description`: The description of the agent (optional). (Inherited from Agent)
   - `Id`: The identifier of the agent (optional). (Inherited from Agent)
   - `Instructions`: The instructions of the agent (optional). (Inherited from KernelAgent)
   - `IsDeleted`: Set when the assistant has been deleted via DeleteAsync(CancellationToken). An assistant removed by other means will result in an exception when invoked.
   - `Kernel`: The Kernel containing services, plugins, and filters for use throughout the agent lifetime. (Inherited from KernelAgent)
   - `Logger`: The ILogger associated with this Agent. (Inherited from Agent)
   - `LoggerFactory`: A ILoggerFactory for this Agent. (Inherited from Agent)
   - `Name`: The name of the agent (optional). (Inherited from Agent)

When executing an Agent that was defined declaratively some of the properties will be determined by the runtime:

- `Kernel`: The runtime will be responsible for create the `Kernel` instance to be used by the Agent. This `Kernel` instance must be configured with the models and tools that the Agent requires.
- `Logger` or `LoggerFactory`: The runtime will be responsible for providing a correctly configured `Logger` or `LoggerFactory`.
- **Functions**: The runtime must be able to resolve any functions required by the Agent. E.g. the VSCode extension will provide a very basic runtime to allow developers to test Agents and it should be able to resolve `KernelFunctions` defined in the current project. See later in the ADR for an example of this.

For Agent properties that define behaviors e.g. `HistoryReducer` the Semantic Kernel **SHOULD**:

- Provide implementations that can be configured declaratively i.e., for the most common scenarios we expect developers to encounter.
- Allow implementations to be resolved from the `Kernel` e.g., as required services or possibly `KernelFunction`'s.

## Decision Drivers

- Schema **MUST** be Agent Service agnostic i.e., will work with Agents targeting Azure, Open AI, Mistral AI, ...
- Schema **MUST** allow model settings to be assigned to an Agent.
- Schema **MUST** allow tools (e.g. functions, code interpreter, file search, ...) to be assigned to an Agent.
- Schema **MUST** allow new types of tools to be defined for an Agent to use.
- Schema **MUST** allow a Semantic Kernel prompt (including Prompty format) to be used to define the Agent instructions.
- Schema **MUST** be extensible so that support for new Agent types with their own settings and tools, can be added to Semantic Kernel.
- Schema **MUST** allow third parties to contribute new Agent types to Semantic Kernel.
- … <!-- numbers of drivers can vary -->

The document will describe the following use cases:

1. Metadata about the agent and the file.
2. Creating an Agent with access to function tools and a set of instructions to guide it's behavior.
3. Allow templating of Agent instructions (and other properties).
4. Configuring the model and providing multiple model configurations.
5. Configuring data sources (context/knowledge) for the Agent to use.
6. Configuring additional tools for the Agent to use e.g. code interpreter, OpenAPI endpoints, .
7. Enabling additional modalities for the Agent e.g. speech.
8. Error conditions e.g. models or function tools not being available.

### Out of Scope

- This ADR does not cover the multi-agent declarative format or the process declarative format

## Considered Options

- Use the [Declarative agent schema 1.2 for Microsoft 365 Copilot](https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/declarative-agent-manifest-1.2)
- Extend the Declarative agent schema 1.2 for Microsoft 365 Copilot
- Extend the [Semantic Kernel prompt schema](https://learn.microsoft.com/en-us/semantic-kernel/concepts/prompts/yaml-schema#sample-yaml-prompt)

## Pros and Cons of the Options

### Use the Declarative agent schema 1.2 for Microsoft 365 Copilot

Semantic Kernel already has support this, see the [declarative Agent concept sample](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/Agents/DeclarativeAgents.cs).

- Good, this is an existing standard adopted by the Microsoft 365 Copilot.
- Neutral, the schema splits tools into two properties i.e. `capabilities` which includes code interpreter and `actions` which specifies an API plugin manifest.
- Bad, because it does support different types of Agents.
- Bad, because it doesn't provide a way to specific and configure the AI Model to associate with the Agent.
- Bad, because it doesn't provide a way to use a Prompt Template for the Agent instructions.
- Bad, because `actions` property is focussed on calling REST API's and cater for native and semantic functions.

### Extend the Declarative agent schema 1.2 for Microsoft 365 Copilot

Some of the possible extensions include:

1. Agent instructions can be created using a Prompt Template.
2. Agent Model settings can be specified including fallbacks based on the available models.
3. Better definition of functions e.g. support for native and semantic.

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- …

### Extend the Semantic Kernel Prompt Schema

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- …

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.

<!-- This is an optional element. Feel free to remove. -->

### Consequences

- Good, because {positive consequence, e.g., improvement of one or more desired qualities, …}
- Bad, because {negative consequence, e.g., compromising one or more desired qualities, …}
- … <!-- numbers of consequences can vary -->

<!-- This is an optional element. Feel free to remove. -->

## Validation

{describe how the implementation of/compliance with the ADR is validated. E.g., by a review or an ArchUnit test}

<!-- This is an optional element. Feel free to remove. -->

## More Information

### Code First versus Declarative Format

Below are examples showing the code first and equivalent declarative syntax for creating different types of Agents.

Consider the following use cases:

1. `ChatCompletionAgent`
2. `ChatCompletionAgent` using Prompt Template
3. `ChatCompletionAgent` with Function Calling
4. `OpenAIAssistantAgent` with Function Calling
5. `OpenAIAssistantAgent` with Tools

#### `ChatCompletionAgent`

Code first approach:

```csharp
ChatCompletionAgent agent =
    new()
    {
        Name = "Parrot",
        Instructions = "Repeat the user message in the voice of a pirate and then end with a parrot sound.",
        Kernel = kernel,
    };
```

Declarative Semantic Kernel schema:

```yml
type: chat_completion_agent
name: Parrot
instructions: Repeat the user message in the voice of a pirate and then end with a parrot sound.
```

**Note**:

- `ChatCompletionAgent` could be the default agent type hence no explicit `type` property is required.

#### `ChatCompletionAgent` using Prompt Template

Code first approach:

```csharp
string generateStoryYaml = EmbeddedResource.Read("GenerateStory.yaml");
PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(generateStoryYaml);

ChatCompletionAgent agent =
    new(templateConfig, new KernelPromptTemplateFactory())
    {
        Kernel = this.CreateKernelWithChatCompletion(),
        Arguments = new KernelArguments()
        {
            { "topic", "Dog" },
            { "length", "3" },
        }
    };
```

Agent YAML points to another file, the Declarative Agent implementation in Semantic Kernel already uses this technique to load a separate instructions file.

Prompt template which is used to define the instructions.
```yml
---
name: GenerateStory
description: A function that generates a story about a topic.  
template:
  format: semantic-kernel
  parser: semantic-kernel
inputs:
  - name: topic
    description: The topic of the story.
    is_required: true
    default: dog
  - name: length
    description: The number of sentences in the story.
    is_required: true
    default: 3
---
Tell a story about {{$topic}} that is {{$length}} sentences long.
```

**Note**: Semantic Kernel could load this file directly.

#### `ChatCompletionAgent` with Function Calling

Code first approach:

```csharp
ChatCompletionAgent agent =
    new()
    {
        Instructions = "Answer questions about the menu.",
        Name = "RestaurantHost",
        Description = "This agent answers questions about the menu.",
        Kernel = kernel,
        Arguments = new KernelArguments(new OpenAIPromptExecutionSettings() { Temperature = 0.4, FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() }),
    };

KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
agent.Kernel.Plugins.Add(plugin);
```

Declarative using Semantic Kernel schema:

```yml
---
name: RestaurantHost
name: RestaurantHost
description: This agent answers questions about the menu.
model:
  id: gpt-4o-mini
  options:
    temperature: 0.4
    function_choice_behavior:
      type: auto
      functions:
        - MenuPlugin.GetSpecials
        - MenuPlugin.GetItemPrice
---
Answer questions about the menu.
```

#### `OpenAIAssistantAgent` with Function Calling

Code first approach:

```csharp
OpenAIAssistantAgent agent =
    await OpenAIAssistantAgent.CreateAsync(
        clientProvider: this.GetClientProvider(),
        definition: new OpenAIAssistantDefinition("gpt_4o")
        {
            Instructions = "Answer questions about the menu.",
            Name = "RestaurantHost",
            Metadata = new Dictionary<string, string> { { AssistantSampleMetadataKey, bool.TrueString } },
        },
        kernel: new Kernel());

KernelPlugin plugin = KernelPluginFactory.CreateFromType<MenuPlugin>();
agent.Kernel.Plugins.Add(plugin);
```

Declarative using Semantic Kernel schema:

Using the syntax below the assistant does not have the functions included in it's definition.
The functions must be added to the `Kernel` instance associated with the Agent and will be passed when the Agent is invoked.

```yml
---
name: RestaurantHost
type: openai_assistant
description: This agent answers questions about the menu.
model:
  id: gpt-4o-mini
  options:
    temperature: 0.4
    function_choice_behavior:
      type: auto
      functions:
        - MenuPlugin.GetSpecials
        - MenuPlugin.GetItemPrice
    metadata:
      sksample: true
---
Answer questions about the menu.
``

or

```yml
---
name: RestaurantHost
type: openai_assistant
description: This agent answers questions about the menu.
execution_settings:
  default:
    temperature: 0.4
tools:
  - type: function
    name: MenuPlugin-GetSpecials
    description: Provides a list of specials from the menu.
  - type: function
    name: MenuPlugin-GetItemPrice
    description: Provides the price of the requested menu item.
    parameters: '{"type":"object","properties":{"menuItem":{"type":"string","description":"The name of the menu item."}},"required":["menuItem"]}'
---
Answer questions about the menu.
```

**Note**: The `Kernel` instance used to create the Agent must have an instance of `OpenAIClientProvider` registered as a service.

#### `OpenAIAssistantAgent` with Tools

Code first approach:

```csharp
OpenAIAssistantAgent agent =
    await OpenAIAssistantAgent.CreateAsync(
        clientProvider: this.GetClientProvider(),
        definition: new(this.Model)
        {
            Instructions = "You are an Agent that can write and execute code to answer questions.",
            Name = "Coder",
            EnableCodeInterpreter = true,
            EnableFileSearch = true,
            Metadata = new Dictionary<string, string> { { AssistantSampleMetadataKey, bool.TrueString } },
        },
        kernel: new Kernel());
```

Declarative using Semantic Kernel:

```yml
---
name: Coder
type: openai_assistant
tools:
    - type: code_interpreter
    - type: file_search
---
You are an Agent that can write and execute code to answer questions.
```

### Declarative Format Use Cases

#### Metadata about the agent and the file

```yaml
name: RestaurantHost
type: azureai_agent
description: This agent answers questions about the menu.
version: 0.0.1
```

#### Creating an Agent with access to function tools and a set of instructions to guide it's behavior

#### Allow templating of Agent instructions (and other properties)

#### Configuring the model and providing multiple model configurations

#### Configuring data sources (context/knowledge) for the Agent to use

#### Configuring additional tools for the Agent to use e.g. code interpreter, OpenAPI endpoints

#### Enabling additional modalities for the Agent e.g. speech

#### Error conditions e.g. models or function tools not being available
