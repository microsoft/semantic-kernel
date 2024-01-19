---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: gitri-ms
date: 2023-12-08
deciders: gitri-ms, alliscode, stephentoub
consulted: 
informed: 
---
# ToolCallBehavior Properties

## Context and Problem Statement

[Task 4300](https://github.com/microsoft/semantic-kernel/issues/4300) is underway to use automatic tool calling in the `FunctionCallingStepwisePlanner`. This will allow for more robust and consistent handling of tool calls and minimize duplication of code.

Currently, as part of the planner configuration, the caller can set the `MaxIterations` field to limit the number of steps (and therefore, calls to the model) utilized by the planner. This enables the caller to control things such as cost, time, etc., spent by the planner.

The current implementation of automatic tool calling allows for multiple consecutive tool calls to be requested/invoked by the model for a single request. However, the limit on how many consecutive tool calls can be performed per request is not exposed to the caller. Therefore, the caller cannot control or even understand how many model roundtrips occur for a single request.

At a minimum
- control OR measure how many calls to model were made per request (iterations)
    - should tool_call -> invoke -> model response based on result (two model RTs) count as one?

## Decision Drivers

1. Keep It Simple - minimize confusion about which properties need to be set and when (give control without confusion)
2. Do not expose more than necessary

## Considered Options

### Option #1: Make the `ToolCallBehavior.MaximumUseAttempts` property public

Expose the `ToolCallBehavior.MaximumUseAttempts` property so that the caller can modify it to fit their needs. Currently this property is internal, and set to `1` for `ToolCallBehavior.RequireFunction` and `int.MaxValue` for all other implementations of `ToolCallBehavior`. Once it is exceeded, the kernel will stop using tools and request a regular chat response from the model.

This is the simplest option that will enable the planner to accurately enforce the `MaxIterations` limit defined in its configuration. The planner could set this value to `1`, so that each iteration of the planner would map to two model round trips (one tool call and one subsequent chat response).

Updated _FunctionCallingStepwisePlanner.cs_ - the commented line has been added

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

However, this approach does not address the gap in being able to measure the number of consecutive tool calls/model round trips that are performed for a single request if `ToolCallBehavior.MaximumUseAttempts` is left to its default value.


### Option #2: Store number of model iterations in chat response metadata

Same as Option #1, but adds an `Iterations` field to the `ChatMessageContent` response metadata.




### Option #3: Add a pre-invoke callback to `ToolCallBehavior`

Add a PreInvokeCallback field to ToolCallBehavior. This callback would be invoked inside `ClientCore.cs` before a tool call is invoked. If `true`, would proceed with the tool call invocation.


- Gives caller ability to decide if they want to invoke tool on the fly / dependent on situation
- **Open question:** if returns false, what happens? We already have a tool call, so the tool would have to be invoked / add result to chat history -- or tool cool would need to be removed from chat history
- Con: this is confusing, why use this vs. not use auto invoke?
Leverage our code for invoking functions, but still give control


In the case of the planner, the planner could utilize this callback to check if a subsequent tool call would exceed the max number of iterations. If so, 

(Really we want to check *before* calling the model though... right?)


## Decision Outcome

TBD

