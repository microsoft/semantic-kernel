---
# These are optional elements. Feel free to remove any of them.
status: { proposed }
date: { 2023-11-13 }
deciders: SergeyMenshykh, markwallace-microsoft, rogerbarreto
consulted:
informed:
---

# How to handle streaming API Changes in Azure SDK beta 9

## Context and Problem Statement

Azure Sdk changes their interface for streaming API in beta 9. This change is not backward compatible and requires changes in our code.
The changes include making some of the streaming interfaces simpler as it assumes the majority of the callers are not handling multiple choices for chat or text completion models.

This also adds new models on how the changes will be passed down in stream of both chat and text completion.

Therefore as Semantic Kernel internal implementations is considering the multiple choices as a common scenarios some options below are provided as the possible solutions for this change.

## User Stories

1. As an SK developer I want to be able to keep using the IChatCompletions and ITextCompletions interfaces with my previous knowledge.
2. As an SK developer in a multiple choice result I want to be able to choose individual choices without changing my current implementation to manage the different streaming choices indexes that can come out of order in the streaming.

```csharp

Task StreamingChatCompletionAsync(IChatCompletion chatCompletion)
{
    List<Task> resultTasks = new();

    // As the user I'm able to choose individual choices if I want to.
    await foreach (var completionResult in chatCompletion.GetStreamingChatCompletionsAsync(chatHistory, requestSettings))
    {
        resultTasks.Add(ProcessStreamAsyncEnumerableAsync(completionResult, currentResult++, consoleLinesPerResult));
    }

    await Task.WhenAll(resultTasks.ToArray());
}

Task ProcessStreamAsyncEnumerableAsync(IChatStreamingResult result)
{
    // As the user I don't have the hasle of managing which choice to use as the results are already for a given choice.
    await foreach (var chatMessage in result.GetStreamingChatMessageAsync())
    {
        Console.Write(chatMessage.Content);
    }
}
```

## Option 1 - Keep interfaces intact, managing the choices streaming internally

In this approach we'll keep the same behavior as it was expected by the users. The changes will be limited to internal changes in components which will allow multiple streaming choices to be handled per choice basis by the users.

With the new flattened streaming API we'll need to keep track of the choices and their indexes as they arrive in the streaming data. This will allow us to provide the correct choice to the user when they request it. To be able to provide the choice abstraction back, the changes demanded a background working approach where the stream is managed internally changing the choices details by reference as the data arrives.

Internals logic change from ClientBase.cs (Similar to streaming text completions)

```csharp
var cachedChoices = new Dictionary<int, List<StreamingChatCompletionsUpdate>>();
var results = new List<ChatStreamingResult>();
bool streamingStarted = false;
bool streamingEnded = false;

// Keep running the request stream in the background populating the updated choices cache
// This will keep the behavior similar to previous versions of the Azure SDK allowing return of Choices to be iterated over
_ = Task.Run(async () =>
{
    await foreach (StreamingChatCompletionsUpdate update in response)
    {
        // Stores the streaming updates by index in
        if (!cachedChoices.ContainsKey(update.ChoiceIndex ?? 0))
        {
            cachedChoices.Add(update.ChoiceIndex ?? 0, new());
            cachedChoices[update.ChoiceIndex ?? 0].Add(update);

            var result = new ChatStreamingResult(cachedChoices[update.ChoiceIndex ?? 0]);
            results.Add(result);
        }
        else
        {
            cachedChoices[update.ChoiceIndex ?? 0].Add(update);
        }

        if (!streamingStarted)
        {
            streamingStarted = true;
        }
    }

    // Updates all results to flag end of stream
    streamingEnded = true;
    foreach (var result in results)
    {
        result.EndOfStream();
    }
}, cancellationToken);

// Wait for streaming to start
while (!streamingStarted)
{
    await Task.Delay(10, cancellationToken).ConfigureAwait(false);
}

// Iterate over all the created choices and return
var i = 0;
while (i < results.Count)
{
    yield return results[i];

    i++;

    // Wait until any new choices were created before the end of the stream
    while (!streamingEnded && i >= results.Count)
    {
        await Task.Delay(50, cancellationToken).ConfigureAwait(false);
    }
}
```

Internals change to `ChatStreamingResult.cs` (similar to `TextStreamingResult.cs`)

```csharp

 string role = string.Empty;
 int i = 0;
 CompletionsFinishReason? finishReason = null;
 string? messageId = null;
 DateTimeOffset? created = null;

while (i < this._chatUpdates.Count)
{
    var message = this._chatUpdates[i];

    // The role will be passed to further messages as soon it is updated
    if (string.IsNullOrEmpty(role) && message.Role.HasValue)
    {
        role = message.Role.Value.ToString();
    }

    if (message.FinishReason.HasValue)
    {
        finishReason = message.FinishReason.Value;
    }

    if (!string.IsNullOrEmpty(message.Id))
    {
        messageId = message.Id;
    }

    if (message.Created != default)
    {
        created = message.Created;
    }

    if (message.ContentUpdate is { Length: > 0 })
    {
        yield return new SKChatMessage(role, message.ContentUpdate, new() { { nameof(message.ContentUpdate), message.ContentUpdate } });
    }

    // This part may change to expose the function name and arguments as new properties of a message
    if (message.FunctionName?.Length > 0 || message.FunctionArgumentsUpdate is { Length: > 0 })
    {
        var functionCall = new FunctionCall(message.FunctionName, message.FunctionArgumentsUpdate);
        yield return new SKChatMessage(role, string.Empty, functionCall, new()
        {
            { nameof(message.FunctionName), message.FunctionName! },
            { nameof(message.FunctionArgumentsUpdate), message.FunctionArgumentsUpdate },
        });
    }

    i++;

    // Wait for next choice update...
    while (!this._isStreamEnded && i >= this._chatUpdates.Count)
    {
        await Task.Delay(50, cancellationToken).ConfigureAwait(false);
    }
}
```

### Pros

- No change in the usage of IText/IChatCompletion interfaces
- When streaming different choices the content can be iterated per choice basis without the need to manage the choice index.
- The user will be able to choose individual choices if they want to.
- Abstractions from Kernel.RunAsync for functions potentially will be abstracting away the different answers on the IText/IChatStreamingResults.

### Cons

- Handling choices internally will require a background task to read the streaming data and update the choices and choice bits on the fly.
- The user will need to iterate over the results even when there's only one choice.

## Option 2 - Break interfaces, leaving to the caller to handle different streaming pieces.

This option surface the streaming pieces as they arrive in the streaming data. This approach is similar to the actual Azure SDK approach, which handles multiple choices scenarios to be handled by the developer manually.

Will be the responsibility of the developer to iterate and manage multiple choices using the `ChoiceIndex` / `ResultIndex` manually.

```csharp

Dictionary<int, string> myChoices = new();
await foreach(var chatUpdate in chatCompletion.GetStreamingChatCompletionsAsync(chatHistory, requestSettings))
{
    // Choice-specific information will provide a ChoiceIndex that allows
    // StreamingChatCompletionsUpdate data for independent choices to be appropriately separated.

    int choiceIndex = chatUpdate.ChoiceIndex.Value;
    if (chatUpdate.Role.HasValue)
    {
        if (myChoices.ContainsKey(choiceIndex))
        {
            myChoices[choiceIndex] += $"{chatUpdate.Role.Value}: ";
        }
        else
        {
            myChoices.Add(choiceIndex, $"{chatUpdate.Role.Value}: ");
        }
    }

    if (!string.IsNullOrEmpty(chatUpdate.ContentUpdate))
    {
        if (myChoices.ContainsKey(choiceIndex))
        {
            myChoices[choiceIndex] += chatUpdate.ContentUpdate;
        }
        else
        {
            myChoices.Add(choiceIndex, chatUpdate.ContentUpdate);
        }
    }
}
```

### Pros

1. Less internal changes to handle the streaming data.
1. Removal of the responsibility on the interfaces to handle different choices/results per request.

### Cons

1. Lack of multiple results abstraction on the IText/IChatCompletion interfaces.
1. The user will need to handle the different choices manually and know the underlying streaming data structure to be able to handle the different choices from other providers **defeating the purpose of the abstraction**.

## Decision Outcome

Chosen option: **Option 1**, reasons:

1. It keeps the multiple results abstraction present
2. Is best aligned with the **User Stories**.
3. No breaking changes for users, and no need to change the public interfaces.
