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

Its very common in co-pilot implementations to have a streamlined output of messages from the LLM and currently that's not possible while using ISKFunctions.InvokeAsync or Kernel.RunAsync methods, which enforces users to work around the Kernel and Functions to use `ITextCompletion` and `IChatCompletion` services directly which currently support this feature.

But notably streaming in its current state is not supported by all providers and this should be added as part or our design to ensure it as a capability the service with a proper abstraction to support also streaming of other types of data like images, audio, video, etc.

Needs to be clear for Kernel when a connector that supports a specific input/output mimetype is available to be used in the function to function pipeline.

Needs to be clear for the Kernel when a connector returns a stream how to build the final result from the bits of data returned by the connector in streaming mode, so this information can be appended and passed down to the next function in the pipeline and the streaming can continue.

## Decision Drivers

- Connectors should be able to flag they have Streaming capability and the Kernel should be able to use it.
- Users should be able to use Kernel to get streaming results.
- Users should be able to use Functions to get streaming results.
- Streaming results can be represented as non streaming results, so getting streaming first approach eventually will be able to support non streaming results.
- Having streaming dedicated methods in Kernel or Functions allow the caller to know what result to expect and implement accordingly.

## User experience goal

abstract StreamingResultBit
string mimeType;
object Value;

StreamingFunctionResult
StreamingResultBuilder<object> Builder;
string mimeType;
Dictionary<string, object> Metadata;
IAsyncEnumerable<StreamingResultBit> StreamingValue;

// Abstractions to make clear how to build a streaming result from streaming bits enumerations
StreamingResultBuilder<TComplete,TBit>
string mimeType;
TComplete Build();
void Append(TBit streamingBit);

// Abstraction of a streaming bit
StreamingResultBit<TBit>
Type streamingBuilder
string mimeType;
TBit streamingBit;

// Abstract connector modality interface
IConnectorModalityService
string string[] inputMimeTypes;
string string outputMimeType;
AsyncEnumerable<StreamingResultBit> GetStreamingResult(object input);
StreamingResultBuilder<TComplete> GetStreamingResultBuilder(string inputMimeType, string outputMimeType);

// Generic version of connector modality interface
IConnectorModalityService<TBit, TComplete> : IConnectorModalityService
string string[] inputMimeTypes;
string string outputMimeType;
AsyncEnumerable<TBit> GetStreamingResult(T input);
StreamingResultBuilder<TComplete> GetStreamingResultBuilder();

//
IServiceSelector
IConnectorModalityService GetServiceByModality(config.inputMimeType ?? "text/plain", config.outputMimeType ?? "text/plain");

// Function

StreamingFunctionResult StreamingInvokeAsync()
{

    (IConnectorModalityService service, var defaultRequestSettings) = serviceSelector.GetServiceByModality(renderedPrompt, context.ServiceProvider, this._modelSettings);

    var resultBuilder = service.GetStreamingResultBuilder(defaultRequestSettings);
    FunctionResult result = new StreamingFunctionResult(this.Name, this.PluginName, context, service.GetStreamingResult) {
        Metadata = new() {
            { "Usage", defaultRequestSettings.InputMimeType },
            { "outputMimeType", defaultRequestSettings.OutputMimeType },
        }
    };
    }

}

```
var kernel = new KernelBuilder()
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, openAIApiKey)
    .Build();

var summarizeFunctions = kernel.ImportSemanticFunctionsFromDirectory(RepoFiles.SamplePluginsPath(), "SummarizePlugin");

await foreach (var resultBit = await kernel.StreamingRunAsync(ask, searchFunctions["Search"]))
{
    Console.Write(resultBit);
}
```

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
