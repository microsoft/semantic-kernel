---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: bentho
date: September 20, 2024
deciders: bentho, markwallace, estenori, crickman, eavanvalkenburg, evchaki
consulted: bentho, markwallace, estenori, crickman, eavanvalkenburg, evchaki, mabolan
informed: SK-3P-FTE
---

# Business Process execution with Semantic Kernel

## Context and Problem Statement

We have heard from many customers about the need for an enterprise grade solution for automating AI-integrated business processes.
At a high level, the structure of a business process is:

- Starts with external event
- Contains a collection of structured activities or tasks
- A defined sequence of these tasks that produces a service or product that adds value
- Serves a business goal

In technical terms, a process is something that can be represented as a graph where nodes in the graph represent units of work and edges between nodes represent causal activations that may or may not also carry data. There are many examples of graph based workflow engines that are suitable for handling traditional enterprise processes. Examples include GitHub Actions & Workflows, Argo Workflows, Dapr Workflows, and many more. However, the additional requirements for integration with AI adds new requirements that may not be adequately supported by these frameworks. Features such as support for cycles in the graph, dynamically created nodes and edges, node and edge level metadata to support AI driven scenarios, and streamlined integration with AI orchestration are missing examples of things that are not fully supported by any of these.

## Decision Drivers

- Customers should be able to leverage their existing investments in all supported languages of Sematic Kernel.
- Customers should be able to leverage their existing investments in infrastructure.
- Customers should be able to collaborate with their business process peers to build up composable processes.
- Customers should be able to use AI to enhance and streamline the steps within their business processes.
- Customers should be able to control the process flow in a defined and repeatable way.
- Customers should be able to easily model typical AI driven scenarios that may require cycles and dynamic edges.
- Processes should be able to support short lived transient business processes as well as long lived business processes.
- Processes should be able to be run locally, deployed as a single process or or deployed to a distributed service.
- Processes should be able to run and debug locally without additional software or infrastructure.
- Processes should be stateful and able resume from a paused state or a recoverable error.
- Regulated Customers should be able to audit currently running or completed processes end to end.

## Considered Options

### Options #1:

**_Build existing samples on top of existing workflow frameworks_**:
This option was explored with frameworks such as Dapr Workflows, Argo, Durable Tasks, and others. Among the subset or these options that can support the technical requirements listed above, the main concern with these frameworks is the amount of overhead required to work with them. Many of these frameworks require a lot of code and infrastructure to get up and running and require special emulators to run locally which is undesirable. It's important to call out that this option is not mutually exclusive with the others, we may choose to build samples showing SK integrating with other workflow engines even we choose to also go a different route.

### Options #2:

**_Build SK Process library within an existing workflow framework_**:
Of all the frameworks explored, the few that seem closest to meeting the technical requirements listed above are based on Durable Tasks. This includes things like Dapr Workflows, Azure Durable Functions, and Azure Durable Tasks Library. Attempts to build a working solution on these frameworks resulted an awkward interface due to the underlying structure of Durable Tasks where nodes are stateless and only the central orchestrator is stateful.

### Options #3:

**_Build SK Process library with a custom build workflow engine_**:
Building a custom workflow engine might provide the cleanest integration but would require extensive resources and time that we don't have. Distributed workflow engines are products in and of themselves.

### Options #4:

**_Build platform agnostic SK Process library with connectors for existing workflow frameworks_**:
This is the chosen option.

## Decision Outcome

**_Chosen option - #4_**: Build platform agnostic SK Process library with connectors for existing workflow frameworks.
This was the only option that was ale to meet all the technical and scenario driven requirements. This option should allow for a simple and well-integrated interface into Semantic Kernel as well as the ability to support many existing distributed runtimes that will give our customers the flexibility to use their existing infrastructure and expertise.

### Components of the Process library

Starting from the ground up, the components of a processes are:

1.  **_KernelFunctions_**: The same KernelFunctions that our customers already know and use. Nothing new here.
1.  **_Steps_**: Steps group one ore more KernelFunctions together into an object with optional user defined state. A step represents one unit of work within a process. Steps make the output of their work visible to other steps in the process by emitting events. This event based structure allows steps to be created without needing to know which process they are used in, allowing them to be reusable across multiple processes.
1.  **_Process_**: A process groups multiple Steps together and defines the way that outputs flow from step to step. The process provides methods that allow the developer to define the routing of events that are emitted by steps by specifying the steps and associated KernelFunctions that should receive the event.

![Basic Process diagram](./diagrams/process/process_diagram_basic.png)

Let's look at the code required to create a simple process.

#### Step1 - Define the Steps:

Steps are required to inherit from the abstract `KernelStepBase` type which allows for optional implementation of activation and deactivation lifecycle methods.

```csharp
// Define UserInputStep with no state
public class UserInputStep : KernelStepBase
{
    public override ValueTask ActivateAsync()
    {
        return ValueTask.CompletedTask;
    }

    [KernelFunction()]
    public string GetUserInput(string userMessage)
    {
        return $"User: {userMessage}";
    }
}

```

The `UserInputStep` shown above is the minimum implementation of a step with 1 KernelFunction and no state management. The code in this step does not explicitly emit any events, however, execution of the `PrintUserMessage` will automatically emit an event indicating either the success of the execution with an associated result, or the failure of the execution with an associated error.

Let's create a second step to take the use input and get a response from an LLM. This step will be stateful so that it can maintain an instance of `ChatHistory`. First define the class to use for tracking state:

```csharp
public class ChatBotState
{
    public ChatHistory ChatMessages { get; set; } = new();
}

```

Next define the step:

```csharp
// Define ChatBotResponseStep with state of type ChatBotState
public class ChatBotResponseStep : KernelStepBase<ChatBotState>
{
    private readonly Kernel _kernel;
    internal ChatBotState? _state;

    public ChatBotResponseStep(Kernel kernel)
    {
        _kernel = kernel;
    }

    public override ValueTask ActivateAsync(ChatBotState state)
    {
        _state = state;
        _state.ChatMessages ??= new();
        return ValueTask.CompletedTask;
    }

    [KernelFunction()]
    public async Task GetChatResponse(KernelStepContext context, string userMessage)
    {
        _state!.ChatMessages.Add(new(AuthorRole.User, userMessage));
        IChatCompletionService chatService = _kernel.Services.GetRequiredService<IChatCompletionService>();
        ChatMessageContent response = await chatService.GetChatMessageContentAsync(_state.ChatMessages);
        if (response != null)
        {
            _state.ChatMessages.Add(response!);
        }

        // emit event: assistantResponse
        context.PostEvent(new CloudEvent { Id = ChatBotEvents.AssistantResponseGenerated, Data = response });
    }
}

```

The `ChatBotResponseStep` is a bit more realistic than `UserInputStep` and show the following features:

**_State management_**: The first thing to notice is that the state object is automatically created by the Process and injected into the `ActivateAsync` method. The Process will automatically persist the state object immediately after successful execution of any of the step's KernelFunctions. Processes use JSON serialization to persist and rehydrate state objects so we require that these types have a default constructor and only contain objects that are JSON serializable.

**_Step Context_**: The `GetChatResponse` KernelFunction has an argument of type `KernelStepContext` which is automatically provided by the Process. This object provides functionality that allow the step to explicitly emit events such as `ChatBotEvents.AssistantResponseGenerated` in this case. The step context can also provide functionality for advances scenarios such as dynamically adding new steps to the process.

**_Cloud Events_**: Events in Steps and Processes make use of [Cloud Events](https://github.com/cloudevents/spec). Cloud Events provide an open source and industry standard specification for describing event data in common formats to provide interoperability across services, platforms and systems. This will allow Processes to emit/receive event to/from external systems without requiring custom connectors or mapping middleware.

#### Step2 - Define the Process:

Now that we have our steps defined, we can move on to defining our process. The first thing to do is to add the steps to the process...

```csharp

KernelProcess process = new("ChatBot");

var userInputStep = process.AddStepFromType<UserInputStep>(isEntryPoint: true);
var responseStep = process.AddStepFromType<ChatBotResponseStep>();

```

The two steps steps created above have been added to our new `ChatBot` process and the `UserInputStep` has been declared as the entry point. This means that any events received by the process will be forwarded to this step. Now we need to define the flow of our process by describing which actions are triggered by events from our steps.

```csharp

// When the userInput step completes, send the output to the llm response step
userInputStep
    .OnFunctionResult(nameof(UserInputStep.GetUserInput))
    .SendOutputTo(responseStep, nameof(ChatBotResponseStep.GetChatResponse), "userMessage");

```

In the code above, `userInputStep.OnFunctionResult(nameof(UserInputStep.GetUserInput))` selects the event that is emitted by the process on successful execution of the `GetUserInput` KernelFunction in the step instance referenced by `userInputStep`. It then returns a builder type object that provides actions based on the context. In this case the `SendOutputTo(responseStep, nameof(ChatBotResponseStep.GetChatResponse), "userMessage")` action is used to forward the event data to the `userMessage` parameter of the `GetChatResponse` KernelFunction on the step instance referenced by `responseStep`.

One of the key takeaways here is that events emitted by a given step can be selected and forwarded to **_a specific parameter of a specific KernelFunction_** within another step. Event data sent to parameters of KernelFunctions are queued until all of the required parameters of the function have received input, at which point the function will be invoked.

#### Step 3 - Get output from the Process:

Now that we've defined our process, we would like to inspect the final result that it produces. In many cases the result of the process will be written to a database or queue or some other internal system and that's all that's needed. In some cases however, such as in the case of a process running in a server as the result of a synchronous REST call, there is a need to extract the result from the finished process so that i can be returned to the caller. In these cases handler functions can be registered on the process to be triggered by a specific event.

Let's wire up the process above to run a handler function when the `ChatBotResponseStep` step completes.

```csharp

process.OnEvent(ChatBotEvents.AssistantResponseGenerated).Run((CloudEvent e) =>
{
    result = (int)e.Data!;
    Console.WriteLine($"Result: {result}");
});

```

#### Step 4 - Run the Process:

## Validation

{describe how the implementation of/compliance with the ADR is validated. E.g., by a review or an ArchUnit test}

## More Information

CodeGen info here

{You might want to provide additional evidence/confidence for the decision outcome here and/or
document the team agreement on the decision and/or
define when this decision when and how the decision should be realized and if/when it should be re-visited and/or
how the decision is validated.
Links to other decisions and resources might appear here as well.}
