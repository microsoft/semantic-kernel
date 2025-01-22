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
Kernel kernel = ...
string agentYaml = EmbeddedResource.Read("MyAgent.yaml");
AgentFactory agentFactory = new AggregatorAgentFactory(
    new ChatCompletionFactory(),
    new OpenAIAssistantAgentFactory(),
    new XXXAgentFactory());
Agent agent = kernel.LoadAgentFromYaml(agentYaml);

ChatHistory chatHistory = new();
chatHistory.AddUserMessage(input);
await foreach (ChatMessageContent content in agent.InvokeAsync(chatHistory))
{
    chatHistory.Add(content);
}
```

**Note:**

1. The above pattern does is not supported at present.
2. We need to decide if the Agent Framework should define an abstraction to allow any Agent to be invoked.
3. If we are supporting an abstraction to allow any Agent to be invoked, what should the pattern look like.
4. We will support JSON also as an out-of-the-box option.

Currently Semantic Kernel supports two Agent types and these have the following properties:

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
2. ['OpenAIAssistantAgent'](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel.agents.agent.description?view=semantic-kernel-dotnet#microsoft-semantickernel-agents-agent-description):
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

When executing an Agent that was declaratively defined some of the properties will be determined by the runtime:

- `Kernel`: The runtime will be responsible for create the `Kernel` instance to be used by the Agent. This `Kernel` instance must be configured with the models and tools that the Agent requires.
- `Logger` or `LoggerFactory`: The runtime will be responsible for providing a correctly configured `Logger` or `LoggerFactory`.
- **Functions**: The runtime must be able to resolve any functions required by the Agent. E.g. the VSCode extension will provide a very basic runtime to allow developers to test Agents and it should eb able to resolve `KernelFunctions` defined in the current project. See later in the ADR for an example of this.

For Agent properties that define behaviors e.g. `HistoryReducer` the Semantic Kernel **SHOULD**:

- Provide implementations that can be configured declaratively i.e., for the most common scenarios we expect developers to encounter.
- Allow implementations to be resolved from the `Kernel` e.g., as required services or possibly `KernelFunction`'s.

## Decision Drivers

- Schema **MUST** allow model settings to be assigned to an Agent
- Schema **MUST** allow functions to be assigned to an Agent
- Schema **MUST** allow a Semantic Kernel prompt to be used to define the Agent instructions
- Schema **MUST** be extensible so that support for new Agent types can be added to Semantic Kernel
- Schema **MUST** allow third parties to contribute new Agent types to Semantic Kernel
- … <!-- numbers of drivers can vary -->

## Considered Options

- Use same semantics as the [Semantic Kernel Prompt Schema](https://learn.microsoft.com/en-us/semantic-kernel/concepts/prompts/yaml-schema#sample-yaml-prompt)
- {title of option 2}

### Use Same Semantics as the Semantic Kernel Prompt Schema

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

Declarative:

```yml
name: Parrot
instructions: Repeat the user message in the voice of a pirate and then end with a parrot sound.
```

**Note**: `ChatCompletionAgent` could be the default agent type hence no explicit `type` property is required.

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

Declarative:

```yml
name: GenerateStory
template: |
  Tell a story about {{$topic}} that is {{$length}} sentences long.
template_format: semantic-kernel
description: A function that generates a story about a topic.
input_variables:
  - name: topic
    description: The topic of the story.
    is_required: true
    default: dog
  - name: length
    description: The number of sentences in the story.
    is_required: true
    default: 3
```

**Note**: Only elements from the prompt template schema are needed.

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

Declarative:

```yml
name: RestaurantHost
instructions: Answer questions about the menu.
description: This agent answers questions about the menu.
execution_settings:
  default:
    temperature: 0.4
    function_choice_behavior:
      type: auto
      functions:
        - MenuPlugin.GetSpecials
        - MenuPlugin.GetItemPrice
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

Declarative:

```yml
name: RestaurantHost
type: openai_assistant
instructions: Answer questions about the menu.
description: This agent answers questions about the menu.
execution_settings:
  gpt_4o:
    function_choice_behavior:
      type: auto
      functions:
        - MenuPlugin.GetSpecials
        - MenuPlugin.GetItemPrice
    metadata:
      sksample: true
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

Declarative:

```yml
name: Coder
type: openai_assistant
instructions: You are an Agent that can write and execute code to answer questions.
execution_settings:
  default:
    enable_code_interpreter: true
    enable_file_search: true
    metadata:
      sksample: true
```

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

## Pros and Cons of the Options

### {title of option 1}

<!-- This is an optional element. Feel free to remove. -->

{example | description | pointer to more information | …}

- Good, because {argument a}
- Good, because {argument b}
<!-- use "neutral" if the given argument weights neither for good nor bad -->
- Neutral, because {argument c}
- Bad, because {argument d}
- … <!-- numbers of pros and cons can vary -->

### {title of other option}

{example | description | pointer to more information | …}

- Good, because {argument a}
- Good, because {argument b}
- Neutral, because {argument c}
- Bad, because {argument d}
- …

<!-- This is an optional element. Feel free to remove. -->

## More Information

{You might want to provide additional evidence/confidence for the decision outcome here and/or
document the team agreement on the decision and/or
define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
how the decision is validated.
Links to other decisions and resources might appear here as well.}
