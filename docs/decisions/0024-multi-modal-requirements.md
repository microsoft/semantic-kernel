# Requirements for long term multi-modal support

## The core scenarios

There are two main scenarios we need to support:

1. A prompt engineer wants to author a prompt YAML file that can support _any_ multi-modal scenario.
2. A professional developer wants to use a connector directly for strongly typed access to the models.

For #2, we believe that our current interfaces for ITextCompletion and IChatCompletion are sufficient for professional developers.
We believe this is true because both the input and output are already strongly typed.

What's not supported today is #1. This is because our Prompt function implementation only can return `FunctionResults` with `ITextResult`
content. To ensure we don't "boil the ocean" it's _ok_ (and expected) that this implementation does not change, however we need to ensure
our interfaces are sufficient to support additional types in the future.

The following sections describe the requirements for #1 and provide scenarios that demonstrate the need for each requirement.

### Requirement #1: Enable "Strongly typed" output for prompt functions

Today, native functions can specify the return type of the function, but this is not possible for prompt functions.

#### The problem

Because prompts can't define their output, it is ambiguous what the return type of the prompt should be.

```yaml
template: |
  <message role="system">
  You are a helpful bot.
  </message>
  <message role="user">
  Can you get me an image of a {{topic}}?
  </message>
template_format: handlebars
description: Creates an image of the specified topic
name: CreateImage
input_parameters:
  - name: name
    description: The name of the person to greet
    default_value: John
  - name: language
    description: The language to generate the greeting in
    default_value: English
```

Based on this example prompt, the return type could be one of the following:

- String
- Image
- Function call
- Chat message (which could be a combination of any of the above)

Because of this ambiguity, the `IAIServiceSelector` does not have enough information to determine which service should be used to process the prompt.
As a result, the `IAIServiceSelector` may choose to select an `ITextCompletion` service (which only returns text) when the prompt engineer really wanted an
`IImageGeneration` service (which returns an image).

For example, the following code would not work as expected if the `IAIServiceSelector` returned an `ITextCompletion` service.

```csharp
// During invocation the IAIServiceSelector could select an ITextCompletion service because it doesn't know better...
FunctionResult chatMessage = await kernel.InvokeAsync(conversationSummaryPlugin["SummarizeConversation"], ChatTranscript);

// Getting the image url would fail because the value is a string
var image = chatMessage.GetValue<Image>().Content
return image.Url;
```

#### Ideal developer experience

Ideally, a Prompt function should be able to specify the return type of the prompt (like native functions). For example, the previous prompt
could be modified to specify the return type as follows:

```yaml
template: |
  <message role="system">
  You are a helpful bot.
  </message>
  <message role="user">
  Can you get me an image of a {{topic}}?
  </message>
template_format: handlebars
description: Creates an image of the specified topic
name: CreateImage
input_parameters:
  - name: name
    description: The name of the person to greet
    default_value: John
  - name: language
    description: The language to generate the greeting in
    default_value: English
output_parameters:
  - description: The image that was generated
    type: Image
```

With this information, the following logic in Semantic Kernel should occur:

- `IAIServiceSelector` should be able to select the correct service to process the prompt. If it does not, an error should be thrown.
- The result within a `FunctionResult` should be the correct type. In this case, it should be an `Image` object.

This also has an additional benefit of sharing with planners and function callers what the return type of the prompt is for chaining.

#### Potential solution

To support the original scenario, the developer could inspect each service in the `IAIServiceSelector` and return back the service that
is _guaranteed_ to return the correct type. For example, the following code could be used to return back an `IImageGeneration` service
whenever the output is specified as an `Image`.

```csharp
private sealed class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, PromptExecutionSettings?) SelectAIService<T>(Kernel kernel, ContextVariables variables, KernelFunction function) where T : class, IAIService
    {
        if (function.Output.Type == type(Image))
        {
            foreach (var service in kernel.GetAllServices<T>())
            {
                // Find the first service that is an IImageGeneration service
                if (service is IImageGeneration)
                {
                    return (service, null);
                }
            }
        }

        // Otherwise, get another service

        throw new KernelException("Unable to find AI service for GPT 3.x.");
    }
}
```

#### Scoping for V1.0.0

To keep V1.0.0 scoped, we should only allow the following types to be returned from a prompt:

- String
- Chat message

_Image, Video, Audio, etc. should be considered for a future release._

### Requirement #2: Standardized prompt input for prompt functions

One of the main values of the template system is that a developer just needs to learn a single template language to be able to use any of the
models. This is because the template system is designed to be a "lowest common denominator" for all models.

For example, the following prompts should be usable by an OpenAI chat completion model, a HuggingFace Chat completion model, or a HuggingFace
Image to text model.

```handlebars
<message role="user">
  Describe this image:
  {{img uploadedImageFile}}
</message>
```

To support this, _somewhere_ there needs to be logic to convert the template into the format the model expects. Today, this logic exists
in the `XmlPromptParser` class and it is used within the connector.

#### The problem

The challenge is that the `XmlPromptParser` class can only be used when the input is a string. This means that the `XmlPromptParser` class
can only be used by `ITextCompletion` services.

This is most acutely felt by the current `FunctionCallingStepwisePlanner`. This planner _should_ be able to use prompt functions to get the
necessary function calls, but it can't because the code path that calls the `XmlPromptParser` class can only return back `ITextResult` objects,
not `IChatResult` objects.

#### Ideal developer experience

Ideally, the `XmlPromptParser` class should be in the code path of all return types. This would allow the `FunctionCallingStepwisePlanner` to
use prompt functions to get the necessary function calls.

#### Potential solution

There are two options where this can happen:

1. In the `InvokeAsync` method of the prompt function
2. In the connectors

Option #1 was previously not chosen because of the fear that it could not scale to the number of model types. Today, for example, there are 39
different model types in the HuggingFace library (as well as a custom model type). Most of these model types have different input schema, so
it's not clear how the `InvokeAsync` method could be implemented in a way that would work for all of them.

By moving the logic to the connector (option #2), each of the 39 model types could have their own implementation that parsed the prompt in the
way that the model expects with the `XmlPromptParser`.

To enforce #2, each service interface would need to require a method that accepted a single string as input with the correct return type.
For example, the `IChatCompletion` interface could require the following four methods:

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    // Existing methods for professional developers
    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        ChatHistory chat,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);

    // New methods for prompt engineers to use with prompt functions
    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(
        string prompt,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);

    IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(
        string prompt,
        dynamic? requestSettings = null,
        CancellationToken cancellationToken = default);
}
```

#### Scoping for V1.0.0

To keep V1.0.0 scoped, we just need to ensure the v1.0.0 interfaces have the methods that require a single string as input so they
can be called by prompt functions. The interfaces that must be updated are:

- ITextCompletion
- IChatCompletion
- And _maybe_ IAIService

_All other services (e.g., IImageGeneration) are marked experimental, so they can be ignored for right now._

### Requirement #3: Make it easy to select a service with a required return type

Today, each of our service interfaces have a unique return type:

- `ITextCompletion`: `ITextResult`
- `IChatCompletion`: `IChatResult`
- `IImageGeneration`: `IImageResult`

This makes it easy for the `IAIServiceSelector` to select the correct service because there's a one-to-one mapping.

#### The problem

In the future, however, there will likely be multiple service interfaces that return the same type. For example, in HuggingFace there are
at least 15 different service types that can return text back (i.e., `ITextResult`). Most (if not all) of these service types will require
different input parameters, so they cannot reuse the `ITextCompletion` interface. Therefore, we'll likely need to introduce the following
interfaces that have the same return type:

- `IImageToTextTask`: `ITextResult`
- `IVisualQuestionAnsweringTask`: `ITextResult` and `IAnswerResult`
- `ITextClassificationTask`: `ITextResult` and `IClassificationResult`
- `ITokenClassificationTask`: `ITextResult` and `IClassificationResult`
- `ITableQuestionAnsweringTask`: `ITextResult` and `ITableAnswerResult`
- `IQuestionAnsweringTask`: `ITextResult`
- `IZeroShotClassificationTask`: `ITextResult` and `IClassificationResult`
- `ITranslationTask`: `ITextResult`
- `ISummarizationTask`: `ITextResult`
- `IConversationTask`: `ITextResult` and `IChatResult`
- `ITextGenerationTask`: `ITextResult`
- `IText2TextGenerationTask`: `ITextResult`
- `IFillMaskTask`: `ITextResult` and `IMaskResult`
- `ISentenceSimilarityTask`: `ITextResult` and `ISimilarityResult`

It is unrealistic to expect the `IAIServiceSelector` to enumerate all of these interfaces _just_ to find a service that returns text.

#### Ideal developer experience

Ideally, the `IAIServiceSelector` should be able to easily deduce the supported output types of a service in a single line of code.

```csharp
private sealed class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, PromptExecutionSettings?) SelectAIService<T>(Kernel kernel, ContextVariables variables, KernelFunction function) where T : class, IAIService
    {
        if (function.Output.Type == type(Image))
        {
            foreach (var service in kernel.GetAllServices<T>())
            {
                // Find the first service that is an IImageGeneration service
                if (service.CanReturn<Image>())
                {
                    return (service, null);
                }
            }
        }

        // Otherwise, get another service

        throw new KernelException("Unable to find AI service for GPT 3.x.");
    }
}
```

#### Potential solution

This could be done in a few ways:

1. The service could have an attribute that specifies the supported output types
2. We create base interfaces that specify the supported output types (e.g., `IReturnsText`, `IReturnsImage`, etc.)
3. Or something else that is way better than the above two options!

#### Scoping for V1.0.0

To keep V1.0.0 scoped, we should prefer any option that can be implemented as a future non-breaking change since this
is technically possible by checking all of the interfaces that implement `IAIService`.
