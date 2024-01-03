## Proposal

### IChatCompletion

Before:

```csharp
public interface IChatCompletion : IAIService
{
    ChatHistory CreateNewChat(string? instructions = null);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, ...);

    Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(string prompt, ...);

    IAsyncEnumerable<T> GetStreamingContentAsync<T>(ChatHistory chatHistory, ...);
}

public static class ChatCompletionExtensions
{
    public static async Task<string> GenerateMessageAsync(ChatHistory chat, ...);
}
```

After:

```csharp
public interface IChatCompletion : IAIService
{
    Task<IReadOnlyList<ChatContent>> GetChatContentsAsync(ChatHistory chat, ..> tags)

    IAsyncEnumerable<StreamingChatContent> GetStreamingChatContentsAsync(ChatHistory chatHistory, ...);
}

public static class ChatCompletionExtensions
{
    //                       v Single          vv Standardized Prompt (Parse <message> tags)
    public static async Task<ChatContent> GetChatContentAsync(string prompt, ...);

    //                       v Single
    public static async Task<ChatContent> GetChatContentAsync(ChatHistory chatHistory, ...);

    public static IAsyncEnumerable<StreamingChatContent> GetStreamingChatContentsAsync(string prompt, ...);
}
```

### ITextCompletion

Before:

```csharp
public interface ITextCompletion : IAIService
{
    Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string prompt, ...);

    IAsyncEnumerable<T> GetStreamingContentAsync<T>(string prompt, ...);
}

public static class TextCompletionExtensions
{
    public static async Task<string> CompleteAsync(string text, ...);

    public static IAsyncEnumerable<StreamingContent> GetStreamingContentAsync(string input, ...);
}
```

After:

```csharp
public interface ITextCompletion : IAIService
{
    Task<IReadOnlyList<TextContent>> GetTextContentsAsync(string prompt, ...);

    IAsyncEnumerable<StreamingTextContent> GetStreamingTextContentsAsync(string prompt, ...);
}

public static class TextCompletionExtensions
{
    public static async Task<TextContent> GetTextContentAsync(string prompt, ...);
}
```

## Content Abstractions

### Model Comparisons

#### Current Streaming Abstractions

| Streaming (Current)                         | Specialized\* Streaming (Current)                               |
| ------------------------------------------- | --------------------------------------------------------------- |
| `StreamingChatContent` : `StreamingContent` | `OpenAIStreamingChatContent`                                    |
| `StreamingTextContent` : `StreamingContent` | `OpenAIStreamingTextContent`, `HuggingFaceStreamingTextContent` |

#### Non-Streaming Abstractions (Before and After)

| Non-Streaming (Before)        | Non-Streaming (After)          | Specialized\* Non-Streaming (After)           |
| ----------------------------- | ------------------------------ | --------------------------------------------- |
| `IChatResult` : `IResultBase` | `ChatContent` : `ModelContent` | `OpenAIChatContent`                           |
| `ITextResult` : `IResultBase` | `TextContent` : `ModelContent` | `OpenAITextContent`, `HuggingFaceTextContent` |
| `ChatMessage`                 | `ChatContent` : `ModelContent` | `OpenAIChatContent`                           |

_\*Specialized: Connector implementations that are specific to a single AI Service._

### New Non-Streaming Abstractions:

`ModelContent` was chosen to represent a `non-streaming content` top-most abstraction which can be specialized and contains all the information that the AI Service returned. (Metadata, Raw Content, etc.)

```csharp
/// <summary>
/// Base class for all AI non-streaming results
/// </summary>
public abstract class ModelContent
{
    /// <summary>
    /// Raw content object reference. (Breaking glass).
    /// </summary>
    public object? InnerContent { get; }

    /// <summary>
    /// The metadata associated with the content.
    /// ⚠️ (Token Usage + More Backend API Metadata) info will be in this dictionary. Old IResult.ModelResult) ⚠️
    /// </summary>
    public Dictionary<string, object?>? Metadata { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="CompleteContent"/> class.
    /// </summary>
    /// <param name="rawContent">Raw content object reference</param>
    /// <param name="metadata">Metadata associated with the content</param>
    protected CompleteContent(object rawContent, Dictionary<string, object>? metadata = null)
    {
        this.InnerContent = rawContent;
        this.Metadata = metadata;
    }
}
```

```csharp
/// <summary>
/// Chat content abstraction
/// </summary>
public class ChatContent : ModelContent
{
    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// Content of the message
    /// </summary>
    public string Content { get; protected set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="chatMessage"></param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public ChatContent(ChatMessage chatMessage, Dictionary<string, object>? metadata = null) : base(chatMessage, metadata)
    {
        this.Role = chatMessage.Role;
        this.Content = chatMessage.Content;
    }
}
```

```csharp
/// <summary>
/// Represents a text content result.
/// </summary>
public class TextContent : ModelContent
{
    /// <summary>
    /// The text content.
    /// </summary>
    public string Text { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TextContent"/> class.
    /// </summary>
    /// <param name="text">Text content</param>
    /// <param name="metadata">Additional metadata</param>
    public TextContent(string text, Dictionary<string, object>? metadata = null) : base(text, metadata)
    {
        this.Text = text;
    }
}
```

### End-User Experience

- No changes to the end-user experience when using `Function.InvokeAsync` or `Kernel.InvokeAsync`
- Changes only when using Connector APIs directly

#### Example 16 - Custom LLMS

Before

```csharp
await foreach (var message in textCompletion.GetStreamingContentAsync(prompt, executionSettings))
{
    Console.Write(message);
}
```

After

```csharp
await foreach (var message in textCompletion.GetStreamingTextContentAsync(prompt, executionSettings))
{
    Console.Write(message);
}
```

#### Example 17 - ChatGPT

Before

```csharp
string reply = await chatGPT.GenerateMessageAsync(chatHistory);
chatHistory.AddAssistantMessage(reply);
```

After

```csharp
var reply = await chatGPT.GetChatContentAsync(chatHistory);
chatHistory.AddMessage(reply);

// OR
chatHistory.AddAssistantMessage(reply.Content);
```

### Clean-up

All old interfaces and classes will be removed in favor of the new ones.
