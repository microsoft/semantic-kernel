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
    /// Adds an wrapper to an instance of <see cref="IChatCompletionService"/> which will use
    /// the provided instance of <see cref="IChatHistoryReducer"/> to reduce the size of
    /// the <see cref="ChatHistory"/> before sending it to the model.
    /// </summary>
    /// <param name="service">Instance of <see cref="IChatCompletionService"/></param>
    /// <param name="reducer">Instance of <see cref="IChatHistoryReducer"/></param>
    public static IChatCompletionService UsingChatHistoryReducer(this IChatCompletionService service, IChatHistoryReducer reducer)
    {
        return new ChatCompletionServiceWithReducer(service, reducer);
    }

    /// <summary>
    /// Returns the first system prompt from the chat history.
    /// </summary>
    internal static ChatMessageContent? GetSystemMessage(this ChatHistory chatHistory)
    {
        return chatHistory.FirstOrDefault(m => m.Role == AuthorRole.System);
    }
}

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which truncates chat history to the provide truncated size.
/// </summary>
/// <remarks>
/// The truncation process is triggered when the list length is great than the truncated size.
/// </remarks>
public sealed class TruncatingChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _truncatedSize;

    /// <summary>
    /// Creates a new instance of <see cref="TruncatingChatHistoryReducer"/>.
    /// </summary>
    /// <param name="truncatedSize">The size of the chat history after truncation.</param>
    public TruncatingChatHistoryReducer(int truncatedSize)
    {
        if (truncatedSize <= 0)
        {
            throw new ArgumentException("Truncated size must be greater than zero.", nameof(truncatedSize));
        }

        this._truncatedSize = truncatedSize;
    }

    /// <inheritdoc/>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken = default)
    {
        var systemMessage = chatHistory.GetSystemMessage();
        var truncationIndex = ComputeTruncationIndex(chatHistory, this._truncatedSize, systemMessage is not null);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex > 0)
        {
            truncatedHistory = chatHistory.Extract(truncationIndex, systemMessage: systemMessage);
        }

        return Task.FromResult<IEnumerable<ChatMessageContent>?>(truncatedHistory);
    }

    #region private
    private static int ComputeTruncationIndex(ChatHistory chatHistory, int truncatedSize, bool hasSystemMessage)
    {
        if (chatHistory.Count <= truncatedSize)
        {
            return -1;
        }

        // Compute the index of truncation target
        var truncationIndex = chatHistory.Count - (truncatedSize - (hasSystemMessage ? 1 : 0));

        // Skip function related content
        while (truncationIndex < chatHistory.Count)
        {
            if (chatHistory[truncationIndex].Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                truncationIndex++;
            }
            else
            {
                break;
            }
        }

        return truncationIndex;
    }
    #endregion
}

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which trim to the specified max token count.
/// </summary>
/// <remarks>
/// This reducer requires that the ChatMessageContent.MetaData contains a TokenCount property.
/// </remarks>
public sealed class MaxTokensChatHistoryReducer : IChatHistoryReducer
{
    private readonly int _maxTokenCount;

    /// <summary>
    /// Creates a new instance of <see cref="MaxTokensChatHistoryReducer"/>.
    /// </summary>
    /// <param name="maxTokenCount">Max token count to send to the model.</param>
    public MaxTokensChatHistoryReducer(int maxTokenCount)
    {
        if (maxTokenCount <= 0)
        {
            throw new ArgumentException("Maimum token count must be greater than zero.", nameof(maxTokenCount));
        }

        this._maxTokenCount = maxTokenCount;
    }

    /// <inheritdoc/>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken = default)
    {
        var systemMessage = chatHistory.GetSystemMessage();

        var truncationIndex = ComputeTruncationIndex(chatHistory, systemMessage);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex > 0)
        {
            truncatedHistory = chatHistory.Extract(truncationIndex, systemMessage: systemMessage);
        }

        return Task.FromResult<IEnumerable<ChatMessageContent>?>(truncatedHistory);
    }

    #region private
    /// <summary>
    /// Compute the index truncation where truncation should begin using the current truncation threshold.
    /// </summary>
    /// <param name="chatHistory">ChatHistory instance to be truncated</param>
    /// <param name="systemMessage">The system message</param>
    private int ComputeTruncationIndex(ChatHistory chatHistory, ChatMessageContent? systemMessage)
    {
        var truncationIndex = -1;

        var totalTokenCount = (int)(systemMessage?.Metadata?["TokenCount"] ?? 0);
        for (int i = chatHistory.Count - 1; i >= 0; i--)
        {
            truncationIndex = i;
            var tokenCount = (int)(chatHistory[i].Metadata?["TokenCount"] ?? 0);
            if (tokenCount + totalTokenCount > this._maxTokenCount)
            {
                break;
            }
            totalTokenCount += tokenCount;
        }

        // Skip function related content
        while (truncationIndex < chatHistory.Count)
        {
            if (chatHistory[truncationIndex].Items.Any(i => i is FunctionCallContent || i is FunctionResultContent))
            {
                truncationIndex++;
            }
            else
            {
                break;
            }
        }

        return truncationIndex;
    }
    #endregion
}

/// <summary>
/// Implementation of <see cref="IChatHistoryReducer"/> which trim to the last N messages and summarizes the remainder.
/// </summary>
public sealed class SummarizingChatHistoryReducer : IChatHistoryReducer
{
    private readonly IChatCompletionService _chatClient;
    private readonly int _truncatedSize;
    private readonly int _summarizationThreshold;
    private readonly string _summarizationPrompt;
    private readonly Kernel _kernel;

    /// <summary>
    /// The default summarization system instructions.
    /// </summary>
    private const string DefaultSummarizationPrompt =
        """
        Provide a concise and complete summarization of the entire dialog that does not exceed 5 sentences

        This summary must always:
        - Consider both user and assistant interactions
        - Maintain continuity for the purpose of further dialog
        - Include details from any existing summary
        - Focus on the most significant aspects of the dialog

        This summary must never:
        - Critique, correct, interpret, presume, or assume
        - Identify faults, mistakes, misunderstanding, or correctness
        - Analyze what has not occurred
        - Exclude details from any existing summary
        """;

    /// <summary>
    /// Metadata key to indicate a summary message.
    /// </summary>
    private const string SummaryMetadataKey = "__summary__";

    /// <summary>
    /// Creates a new instance of <see cref="SummarizingChatHistoryReducer"/>.
    /// </summary>
    /// <param name="chatClient">Instance of <see cref="IChatCompletionService"/> to use for summarization</param>
    /// <param name="truncatedSize">The truncated size of the chat history after summarization is triggered</param>
    /// <param name="summarizationThreshold">The threshold at which to trigger summarization</param>
    /// <param name="summarizationPrompt">An optional prompt to use when summarizing the content</param>
    public SummarizingChatHistoryReducer(IChatCompletionService chatClient, int truncatedSize, int summarizationThreshold, string? summarizationPrompt = null)
    {
        if (chatClient is null)
        {
            throw new ArgumentException("Chat completion service must be specified.", nameof(chatClient));
        }
        if (truncatedSize <= 0)
        {
            throw new ArgumentException("Truncated size must be greater than zero.", nameof(truncatedSize));
        }
        if (summarizationThreshold < truncatedSize)
        {
            throw new ArgumentException($"Summarization threshold must be greater than truncatedSize: {truncatedSize}.", nameof(summarizationPrompt));
        }

        this._chatClient = chatClient;
        this._truncatedSize = truncatedSize;
        this._summarizationThreshold = summarizationThreshold;
        this._summarizationPrompt = summarizationPrompt ?? DefaultSummarizationPrompt;

        var builder = Kernel.CreateBuilder();
        builder.Services.AddTransient<IChatCompletionService>((sp) => chatClient);
        this._kernel = builder.Build();
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<ChatMessageContent>?> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken = default)
    {
        // index of the last summary message
        int lastIndex = chatHistory
            .Select((value, index) => new { value, index })
            .LastOrDefault(message => message.value.Metadata?.ContainsKey(SummaryMetadataKey) ?? false)
            ?.index ?? -1;

        var systemMessage = chatHistory.GetSystemMessage();
        var hasSystemMessage = systemMessage is not null;

        // check are there messages to be summarized
        var startIndex = -1;
        var endIndex = chatHistory.Count - this._truncatedSize + (hasSystemMessage ? 1 : 0);
        if (lastIndex == -1)
        {
            // have never summarized so use chat history size
            if (chatHistory.Count < this._summarizationThreshold)
            {
                return null;
            }
            startIndex = 0 + (hasSystemMessage ? 1 : 0);
        }
        else
        {
            // have summarized so use chat history size minus position of last summary
            if (chatHistory.Count - lastIndex < this._summarizationThreshold)
            {
                return null;
            }
            startIndex = lastIndex;
        }

        IEnumerable<ChatMessageContent>? truncatedHistory = null;
        var summaryMessage = await this.SummarizeAsync(chatHistory, startIndex, endIndex, cancellationToken);

        truncatedHistory = chatHistory.Extract(endIndex + 1, systemMessage: systemMessage, summaryMessage: summaryMessage);

        // insert summary into the original chat history
        if (summaryMessage is not null)
        {
            chatHistory.Insert(endIndex, summaryMessage);
        }

        return truncatedHistory;
    }

    #region private
    /// <summary>
    /// Summarize messages starting at the truncation index.
    /// </summary>
    /// <param name="chatHistory"></param>
    /// <param name="startIndex"></param>
    /// <param name="endIndex"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    private async Task<ChatMessageContent?> SummarizeAsync(ChatHistory chatHistory, int startIndex, int endIndex, CancellationToken cancellationToken)
    {
        // extract history for summarization
        IEnumerable<ChatMessageContent> messagesToSummarize =
            chatHistory.Extract(startIndex, endIndex: endIndex,
                messageFilter: (m) => m.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent));

        // summarize the chat history
        var summarizationRequest = new ChatHistory(this._summarizationPrompt);
        summarizationRequest.AddRange(messagesToSummarize);
        ChatMessageContent? summaryContent = await this._chatClient.GetChatMessageContentAsync(summarizationRequest, cancellationToken: cancellationToken).ConfigureAwait(false);
        summaryContent.Metadata = new Dictionary<string, object?> { { SummaryMetadataKey, true } };

        return summaryContent;
    }
    #endregion
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
    Task<IEnumerable<ChatMessageContent>?> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken);
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
        var reducedMessages = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);
        var history = reducedMessages is null ? chatHistory : new ChatHistory(reducedMessages);

        return await service.GetChatMessageContentsAsync(history, executionSettings, kernel, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
        ChatHistory chatHistory,
        PromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var reducedMessages = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);
        var history = reducedMessages is null ? chatHistory : new ChatHistory(reducedMessages);

        var messages = service.GetStreamingChatMessageContentsAsync(history, executionSettings, kernel, cancellationToken);
        await foreach (var message in messages)
        {
            yield return message;
        }
    }
}
