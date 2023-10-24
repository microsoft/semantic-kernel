---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-09-26
deciders: rbarreto,markwallace,sergey,dmytro
consulted:
informed:
---

# Streaming Capability for Kernel and Functions usage

## Context and Problem Statement

Its very common in co-pilot implementations to have a streamlined output of messages from the LLM and currently that's not possible while using ISKFunctions.InvokeAsync or Kernel.RunAsync methods, which enforces users to work around the Kernel and Functions to use `ITextCompletion` and `IChatCompletion` services directly.

So this ADR propose a solution for the above fore mentioned problem.

## Decision Drivers

- Architecture changes and the associated decision making process should be transparent to the community.
- Decision records are stored in the repository and are easily discoverable for teams involved in the various language ports.
- The solution should be backward compatible with the existing implementations.
- The design should be extensible to support future requirements.
- Keep the design as simple and easy to understand.

## Considered Options

### Streaming Setting + New Streaming Interfaces

This option is to add a new setting `Streaming` to the `AIRequestSettings` definition to flag the caller would like to stream the output from the kernel and functions if possible.

Seggregate old Text/Chat Completion interfaces the into new `ITextStreamingCompletion` and `IChatStreamingCompletion` dedicated for streaming (interface segregation). **This becomes crucial to the Kernel knows if streaming is supported by the service.**

#### Backward compatibility aspects:

- SKContext was built on top of a non streaming functionality, so to keep the compatibility for streaming scenarios, SKContext needs to be updated into a Lazy loading strategy, where when used will enforce the buffering of the whole stream to be able to return to final result.

- Streaming by default will be `false`
  1. It wont force streaming results over legacy implementations.
  2. Providers like OpenAI/Azure OpenAI don't provide additional data like (Usage, Completion Tokens, Prompt Tokens, Total Tokens, ...) in streaming results.

Enable streaming behavior set `Streaming = true` in a `AIRequestSettings` specialized class like `OpenAIRequestSettings`, once this is set for text/chat based models like OpenAi's GPT you can get streaming data using `GetValue<IAsyncEnumerable<string>>()` in the result of `Kernel.RunAsync` or `Function.InvokeAsync`.

Example:

```
myFunction = kernel.CreateSemanticFunction($"your prompt",
        requestSettings: new OpenAIRequestSettings
        {
            Streaming = true,
        });

var result = await kernel.RunAsync(myFunction);
await foreach (string token in result.GetValue<IAsyncEnumerable<string>>())
{
    Console.Write(token);
}
```

## Decision Outcome

As for now, the only proposed solution is the #1.
