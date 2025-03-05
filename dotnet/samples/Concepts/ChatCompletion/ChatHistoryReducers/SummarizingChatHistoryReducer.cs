// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

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
        var endIndex = chatHistory.Count - this._truncatedSize;
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

        var summaryMessage = await this.SummarizeAsync(chatHistory, startIndex, endIndex, cancellationToken);

        // insert summary into the original chat history
        chatHistory.Insert(endIndex + 1, summaryMessage);

        IEnumerable<ChatMessageContent>? truncatedHistory = chatHistory.Extract(endIndex + 2, systemMessage: systemMessage, summaryMessage: summaryMessage);
        return truncatedHistory;
    }

    #region private
    /// <summary>
    /// Summarize messages starting at the truncation index.
    /// </summary>
    private async Task<ChatMessageContent> SummarizeAsync(ChatHistory chatHistory, int startIndex, int endIndex, CancellationToken cancellationToken)
    {
        // extract history for summarization
        IEnumerable<ChatMessageContent> messagesToSummarize =
            chatHistory.Extract(startIndex, endIndex: endIndex,
                messageFilter: (m) => m.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent));

        // summarize the chat history
        var summarizationRequest = new ChatHistory(this._summarizationPrompt);
        summarizationRequest.AddRange(messagesToSummarize);
        ChatMessageContent summaryContent = await this._chatClient.GetChatMessageContentAsync(summarizationRequest, cancellationToken: cancellationToken).ConfigureAwait(false);
        summaryContent.Metadata = new Dictionary<string, object?> { { SummaryMetadataKey, true } };

        return summaryContent;
    }
    #endregion
}
