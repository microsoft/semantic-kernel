// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.CompilerServices;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Extensions methods for <see cref="IChatCompletionService"/>
/// </summary>
internal static class ChatCompletionServiceExtensions
{
    /// <summary>
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will invoke a delegate
    /// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="messageCount">Number of messages to include in the chat history</param>
    public static IChatCompletionService WithTrimmingChatHistoryReducer(this IChatCompletionService service, int messageCount)
    {
        return new ChatCompletionServiceWithReducer(service, new TrimmingChatHistoryReducer(messageCount));
    }

    /// <summary>
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will invoke a delegate
    /// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="maxTokenCount">Maximum number of tokens to be used by <see cref="ChatHistory"/></param>
    public static IChatCompletionService WithMaxTokensChatHistoryReducer(this IChatCompletionService service, int maxTokenCount)
    {
        return new ChatCompletionServiceWithReducer(service, new MaxTokensChatHistoryReducer(maxTokenCount));
    }

    /// <summary>
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will invoke a delegate
    /// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="output"></param>
    /// <param name="systemPrompt"></param>
    /// <param name="summarizationPrompt"></param>
    /// <param name="messageCount">Number of messages to include in the chat history</param>
    public static IChatCompletionService WithSummarizingChatHistoryReducer(this IChatCompletionService service, ITestOutputHelper output, string systemPrompt, string summarizationPrompt, int messageCount)
    {
        return new ChatCompletionServiceWithReducer(service, new SummarizingChatHistoryReducer(output, service, systemPrompt, summarizationPrompt, messageCount));
    }

    /// <summary>
    /// Returns the system prompt from the chat history.
    /// </summary>
    internal static ChatMessageContent? GetSystemMessage(this ChatHistory chatHistory)
    {
        return chatHistory.FirstOrDefault(m => m.Role == AuthorRole.System);
    }
}

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which trim to the last N messages.
/// </summary>
internal sealed class TrimmingChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _messageCount;

    internal TrimmingChatHistoryReducer(int messageCount)
    {
        this._messageCount = messageCount;
    }

    /// <inheritdoc/>
    public Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var systemMessage = chatHistory.GetSystemMessage();
        ChatHistory reducedChatHistory = systemMessage is not null ? new(systemMessage.Content!) : new();
        // trimming to just the last N messages
        reducedChatHistory.Add(chatHistory[^this._messageCount]);
        return Task.FromResult<ChatHistory>(reducedChatHistory);
    }
}

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which trim to the specified max token count.
/// </summary>
internal sealed class MaxTokensChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _maxTokenCount;

    internal MaxTokensChatHistoryReducer(int maxTokenCount)
    {
        this._maxTokenCount = maxTokenCount;
    }

    /// <inheritdoc/>
    public Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        ChatHistory reducedChatHistory = [];
        var totalTokenCount = 0;
        var insertIndex = 0;
        var systemMessage = chatHistory.GetSystemMessage();
        if (systemMessage is not null)
        {
            reducedChatHistory.Add(systemMessage);
            totalTokenCount += (int)(systemMessage.Metadata?["TokenCount"] ?? 0);
            insertIndex = 1;
        }
        // Add the remaining messages that fit within the token limit
        for (int i = chatHistory.Count - 1; i >= 1; i--)
        {
            var tokenCount = (int)(chatHistory[i].Metadata?["TokenCount"] ?? 0);
            if (tokenCount + totalTokenCount > this._maxTokenCount)
            {
                break;
            }
            reducedChatHistory.Insert(insertIndex, chatHistory[i]);
            totalTokenCount += tokenCount;
        }
        return Task.FromResult<ChatHistory>(reducedChatHistory);
    }
}

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which trim to the last N messages and summarizes the remainder.
/// </summary>
internal sealed class SummarizingChatHistoryReducer : IChatHistoryReducer
{
    private readonly ITestOutputHelper _output;
    private readonly IChatCompletionService _service;
    private readonly string _systemPrompt;
    private readonly int _messageCount;
    private readonly KernelFunction _summarizationFunction;
    private readonly Kernel _kernel;

    internal SummarizingChatHistoryReducer(ITestOutputHelper output, IChatCompletionService service, string systemPrompt, string summarizationPrompt, int messageCount)
    {
        this._output = output;
        this._service = service;
        this._systemPrompt = systemPrompt;
        this._messageCount = messageCount;
        this._summarizationFunction = KernelFunctionFactory.CreateFromPrompt(summarizationPrompt);

        var builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => service);
        this._kernel = builder.Build();
    }

    /// <inheritdoc/>
    public async Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        // summarize the chat history
        var summary = await SummarizeAsync(chatHistory, cancellationToken);
        var systemMessage = string.IsNullOrEmpty(summary?.ToString()) ? this._systemPrompt : $"{this._systemPrompt}. USE MOST RECENT INFORMATION FROM FOLLOWING SUMMARY AS CONTEXT FOR QUESTIONS: <SUMMARY START>{summary}<SUMMARY END>";
        ChatHistory reducedChatHistory = new(systemMessage);
        // adding the last N messages
        reducedChatHistory.Add(chatHistory[^this._messageCount]);
        return reducedChatHistory;
    }

    private async Task<string?> SummarizeAsync(ChatHistory chatHistory, CancellationToken cancellationToken)
    {
        var start = chatHistory.Count - this._messageCount - 1;
        if (start < 0)
        {
            return null;
        }

        List<string> messages = new();
        for (int i = start; i >= 0; i--)
        {
            if (chatHistory[i].Metadata?.TryGetValue("Summary", out var summary) == true && summary is not null)
            {
                messages.Add(summary!.ToString()!);
                break;
            }
            var message = chatHistory[i];
            messages.Add($"{message.Role}: {message.Content}");
        }

        // invoke the summarization function
        messages.Reverse();
        var chatMessages = string.Join("\n", messages);
        KernelArguments arguments = new() { { "chat_messages", chatMessages } };
        var result = await this._summarizationFunction.InvokeAsync(this._kernel, arguments, cancellationToken);

        this._output.WriteLine($"\nSUMMARISE: [[{chatMessages}]]");
        this._output.WriteLine($"\nSUMMARY: [[{result.GetValue<string>()}]]");

        // store previous summary in the chat history
        this.AddSummaryToMessage(chatHistory, start, result.GetValue<string>());

        return result.GetValue<string>();
    }

    private void AddSummaryToMessage(ChatHistory chatHistory, int index, string? summary)
    {
        if (string.IsNullOrEmpty(summary))
        {
            return;
        }
        var currentMessage = chatHistory[index];
        ChatMessageContent newMessage = new()
        {
            Role = currentMessage.Role,
            Items = currentMessage.Items,
            ModelId = currentMessage.ModelId,
            InnerContent = currentMessage.InnerContent,
            Encoding = currentMessage.Encoding,
            Metadata = new Dictionary<string, object?>(currentMessage.Metadata)
            {
                ["Summary"] = summary
            }
        };
        chatHistory[index] = newMessage;
    }
}

/// <summary>
/// Interface for reducing the chat history before sending it to the chat completion provider.
/// </summary>
public interface IChatHistoryReducer
{
    /// <summary>
    /// Reduce the <see cref="ChatHistory"/> before sending it to the <see cref="IChatCompletionService"/>.
    /// </summary>
    /// <param name="chatHistory">Instance of <see cref="ChatHistory"/>to be reduced.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    Task<ChatHistory> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken);
}

/// <summary>
/// Instance of <see cref="IChatCompletionService"/> which will invoke a delegate
/// to reduce the size of the <see cref="ChatHistory"/> before sending it to the model.
/// </summary>
internal sealed class ChatCompletionServiceWithReducer(IChatCompletionService service, IChatHistoryReducer reducer) : IChatCompletionService
{
    public IReadOnlyDictionary<string, object?> Attributes => throw new NotImplementedException();

    /// <inheritdoc/>
    public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default)
    {
        var reducedChatHistory = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);

        return await service.GetChatMessageContentsAsync(reducedChatHistory ?? chatHistory, executionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var reducedChatHistory = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);

        var messages = service.GetStreamingChatMessageContentsAsync(reducedChatHistory ?? chatHistory, executionSettings, kernel, cancellationToken);
        await foreach (var message in messages)
        {
            yield return message;
        }
    }
}
