---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: gitri-ms
date: 2024-01-19
deciders:
consulted:
informed:
---

# Automatic Tool Calling Controls

## Context and Problem Statement

[Task 4300](https://github.com/microsoft/semantic-kernel/issues/4300) is underway to use automatic tool calling in the `FunctionCallingStepwisePlanner`. This will allow for more robust and consistent handling of tool calls and minimize duplication of code.

Currently, as part of the planner configuration, the caller can set the `MaxIterations` field to limit the number of steps (and therefore, calls to the model) utilized by the planner. This enables the caller to control things such as cost, time, etc., spent by the planner.

The current implementation of automatic tool calling allows for multiple consecutive tool calls to be requested/invoked by the model for a single request. However, the limit on how many consecutive tool calls can be performed per request is not exposed to the caller. Therefore, the caller cannot control or even measure after the fact how many model roundtrips occur for a single request. This control is necessary for the planner to accurately enforce the `MaxIterations` limit.

## Decision Drivers

1. Developers should be able to control how many tool calls (and subsequent model calls) are performed for a single request
2. Chosen control(s) should be easy for developers to understand and utilize
3. No breaking changes to abstractions
4. Do not expose more than necessary

## Considered Options

### Option #1: Make the `ToolCallBehavior.MaximumUseAttempts` property public

Expose the `ToolCallBehavior.MaximumUseAttempts` property so that the caller can modify it to fit their needs. Currently this property is internal, and set to `1` for `ToolCallBehavior.RequireFunction` and `int.MaxValue` for all other implementations of `ToolCallBehavior`. Once it is exceeded, the kernel will stop using tools and request a regular chat response from the model.

This is the simplest option that will enable the planner to accurately enforce the `MaxIterations` limit defined in its configuration. The planner could set this value to `1`, so that each iteration of the planner would map to two model round trips (one tool call and one subsequent chat response).

Updated helper method in _FunctionCallingStepwisePlanner.cs_:

```csharp
private async Task<ChatMessageContent> GetCompletionWithFunctionsAsync(
    ChatHistory chatHistory,
    Kernel kernel,
    IChatCompletionService chatCompletion,
    OpenAIPromptExecutionSettings openAIExecutionSettings,
    ILogger logger,
    CancellationToken cancellationToken)
{
    openAIExecutionSettings.ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions;
    openAIExecutionSettings.ToolCallBehavior.MaximumUseAttempts = 1; // limit to a single tool call per request

    await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
    return await chatCompletion.GetChatMessageContentAsync(chatHistory, openAIExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
}
```

A downside of this approach is that it does not enable the caller to measure the number of consecutive tool calls/model round trips that were performed for a single request if `ToolCallBehavior.MaximumUseAttempts` was left to its default value.

### Option #2: Store number of model iterations in chat response metadata

Same as Option #1, but adds an `Iterations` field to the `ChatMessageContent` response metadata. This field would be set to the number of model iterations that occurred as a result of the request, as computed inside `ClientCore.GetChatMessageContentsAsync` or `ClientCore.GetStreamingChatMessageContentsAsync`.

Updated helper method in _ClientCore.cs_:

```csharp
private static Dictionary<string, object?> GetResponseMetadata(ChatCompletions completions, int iterations)
{
    return new Dictionary<string, object?>(6)
    {
        { nameof(completions.Id), completions.Id },
        { nameof(completions.Created), completions.Created },
        { nameof(completions.PromptFilterResults), completions.PromptFilterResults },
        { nameof(completions.SystemFingerprint), completions.SystemFingerprint },
        { nameof(completions.Usage), completions.Usage },
        { "Iterations", iterations }
    };
}
```

Updated loop inside `ClientCore.GetChatMessageContentsAsync`:

```csharp
for (int iteration = 1; ; iteration++)
{
    // Make the request.
    var responseData = (await RunRequestAsync(() => this.Client.GetChatCompletionsAsync(chatOptions, cancellationToken)).ConfigureAwait(false)).Value;
    this.CaptureUsageDetails(responseData.Usage);
    if (responseData.Choices.Count == 0)
    {
        throw new KernelException("Chat completions not found");
    }

    IReadOnlyDictionary<string, object?> metadata = GetResponseMetadata(responseData, iteration); // adds iteration in addition to other metadata

    // ...
}
```

The planner could then use this metadata to determine how many model iterations occurred as a result of each request, and enforce the `MaxIterations` limit accordingly. This would also reduce the overall model calls made by the planner, since tool calls could be "chained" consecutively by the kernel rather than having a chat response in between each one (as would be the case with Option 1).

Updated helper method in _FunctionCallingStepwisePlanner.cs_:

```csharp
private async Task<ChatMessageContent> GetCompletionWithFunctionsAsync(
    int currentIteration,
    ChatHistory chatHistory,
    Kernel kernel,
    IChatCompletionService chatCompletion,
    OpenAIPromptExecutionSettings openAIExecutionSettings,
    ILogger logger,
    CancellationToken cancellationToken)
{
    openAIExecutionSettings.ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions;
    openAIExecutionSettings.ToolCallBehavior.MaximumUseAttempts = this.Config.MaxIterations - currentIteration; // limit the number of tool calls to the number of iterations remaining

    await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
    return await chatCompletion.GetChatMessageContentAsync(chatHistory, openAIExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
}
```

Updated loop in _FunctionCallingStepwisePlanner.cs_:

```csharp
for (int iteration = 0; iteration < this.Config.MaxIterations; /* iteration is incremented within the loop */)
{
    // sleep for a bit to avoid rate limiting
    // ...

    // For each step, request another completion to select a function for that step
    chatHistoryForSteps.AddUserMessage(StepwiseUserMessage);
    var chatResult = await this.GetCompletionWithFunctionsAsync(iteration, chatHistoryForSteps, clonedKernel, chatCompletion, stepExecutionSettings, logger, cancellationToken).ConfigureAwait(false);
    chatHistoryForSteps.Add(chatResult);

    // Increment iteration based on the number of model round trips that occurred as a result of the request
    object? value = null;
    chatResult.Metadata?.TryGetValue("Iterations", out value);
    if (value is not null and int)
    {
        iteration += (int)value;
    }
    else
    {
        // Could not find iterations in metadata, so assume just one
        iteration++;
    }

    // Check for final answer
    // ...
}
```

### Option #3: Add a pre-invoke callback to `ToolCallBehavior`

Add a PreInvokeCallback field to `ToolCallBehavior`. This callback would be invoked inside `ClientCore.cs` before a tool call is invoked. If `true`, would proceed with the tool call invocation. This approach would give the caller control over whether or not a tool call is invoked, while still leveraging the kernel's code for invocation.

The planner could utilize this callback to check if a subsequent tool call would exceed the maximum number of iterations for the planner, and choose to bail out accordingly. However, to accurately measure this, the planner would also require the `Iterations` metadata field from Option #2.

- **Open question:** If the callback returns `false`, what should happen?
  - A `tool_call` must be followed by a `tool` result in the chat history, so either the tool would need to be invoked, or the `tool_call` would need to be removed in order to maintain a valid chat history.
  - If the `tool_call` is removed, would we then ask for another completion (without tools)? This could result in unnecessary calls to the model (and additional expense).
  - Could return the `tool_call` result to the caller and let them decide what to do.

Updated _ToolCallBehavior.cs_:

```csharp
public delegate bool ToolCallPreInvokeCallback(int iteration, string toolName, string[] toolArgs);

/// <summary>Represents a behavior for OpenAI tool calls.</summary>
public abstract class ToolCallBehavior
{
    /// <summary>Optional callback indicating whether to proceed with the tool call.</summary>
    public ToolCallPreInvokeCallback? PreInvokeCallback { get; set; }

    // ...
}
```

Updated helper method in _FunctionCallingStepwisePlanner.cs_:

```csharp
private async Task<ChatMessageContent> GetCompletionWithFunctionsAsync(
    int currentIteration,
    ChatHistory chatHistory,
    Kernel kernel,
    IChatCompletionService chatCompletion,
    OpenAIPromptExecutionSettings openAIExecutionSettings,
    ILogger logger,
    CancellationToken cancellationToken)
{
    openAIExecutionSettings.ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions;

    int iterationsRemaining = this.Config.MaxIterations - currentIteration;
    openAIExecutionSettings.ToolCallBehavior.PreInvokeCallback = (iteration, _, _) => { return (iteration < iterationsRemaining); }; // only proceed with tool call if there are iterations remaining for the plan

    await this.ValidateTokenCountAsync(chatHistory, kernel, logger, openAIExecutionSettings, cancellationToken).ConfigureAwait(false);
    return await chatCompletion.GetChatMessageContentAsync(chatHistory, openAIExecutionSettings, kernel, cancellationToken).ConfigureAwait(false);
}
```

## Decision Outcome

TBD
