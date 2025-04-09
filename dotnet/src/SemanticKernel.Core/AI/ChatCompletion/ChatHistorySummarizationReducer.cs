// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Reduce the chat history by summarizing message past the target message count.
/// </summary>
/// <remarks>
/// Summarization will always avoid orphaning function-content as the presence of
/// a function-call _must_ be followed by a function-result.  When a threshold count is
/// is provided (recommended), reduction will scan within the threshold window in an attempt to
/// avoid orphaning a user message from an assistant response.
/// </remarks>
public class ChatHistorySummarizationReducer : IChatHistoryReducer
{
    /// <summary>
    /// Metadata key to indicate a summary message.
    /// </summary>
    public const string SummaryMetadataKey = "__summary__";

    /// <summary>
    /// The default summarization system instructions.
    /// </summary>
    public const string DefaultSummarizationPrompt =
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
    /// System instructions for summarization.  Defaults to <see cref="DefaultSummarizationPrompt"/>.
    /// </summary>
    public string SummarizationInstructions { get; init; } = DefaultSummarizationPrompt;

    /// <summary>
    /// Flag to indicate if an exception should be thrown if summarization fails.
    /// </summary>
    public bool FailOnError { get; init; } = true;

    /// <summary>
    /// Flag to indicate summarization is maintained in a single message, or if a series of
    /// summations are generated over time.
    /// </summary>
    /// <remarks>
    /// Not using a single summary may ultimately result in a chat history that exceeds the token limit.
    /// </remarks>
    public bool UseSingleSummary { get; init; } = true;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistorySummarizationReducer"/> class.
    /// </summary>
    /// <param name="service">A <see cref="IChatCompletionService"/> instance to be used for summarization.</param>
    /// <param name="targetCount">The desired number of target messages after reduction.</param>
    /// <param name="thresholdCount">An optional number of messages beyond the 'targetCount' that must be present in order to trigger reduction/</param>
    /// <remarks>
    /// While the 'thresholdCount' is optional, it is recommended to provided so that reduction is not triggered
    /// for every incremental addition to the chat history beyond the 'targetCount'.
    /// </remarks>>
    public ChatHistorySummarizationReducer(IChatCompletionService service, int targetCount, int? thresholdCount = null)
    {
        Verify.NotNull(service, nameof(service));
        Verify.True(targetCount > 0, "Target message count must be greater than zero.");
        Verify.True(!thresholdCount.HasValue || thresholdCount > 0, "The reduction threshold length must be greater than zero.");

        this._service = service;
        this._targetCount = targetCount;
        this._thresholdCount = thresholdCount ?? 0;
    }

    /// <inheritdoc/>
    public async Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> chatHistory, CancellationToken cancellationToken = default)
    {
        var systemMessage = chatHistory.FirstOrDefault(l => l.Role == AuthorRole.System);

        // Identify where summary messages end and regular history begins
        int insertionPoint = chatHistory.LocateSummarizationBoundary(SummaryMetadataKey);

        // First pass to determine the truncation index
        int truncationIndex = chatHistory.LocateSafeReductionIndex(
            this._targetCount,
            this._thresholdCount,
            insertionPoint,
            hasSystemMessage: systemMessage is not null);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex >= 0)
        {
            // Second pass to extract history for summarization
            IEnumerable<ChatMessageContent> summarizedHistory =
                chatHistory.Extract(
                    this.UseSingleSummary ? 0 : insertionPoint,
                    truncationIndex,
                    filter: (m) => m.Items.Any(i => i is FunctionCallContent || i is FunctionResultContent));

            try
            {
                // Summarize
                ChatHistory summarizationRequest = [.. summarizedHistory, new ChatMessageContent(AuthorRole.System, this.SummarizationInstructions)];
                ChatMessageContent summaryMessage = await this._service.GetChatMessageContentAsync(summarizationRequest, cancellationToken: cancellationToken).ConfigureAwait(false);
                summaryMessage.Metadata = new Dictionary<string, object?> { { SummaryMetadataKey, true } };

                // Assembly the summarized history
                truncatedHistory = AssemblySummarizedHistory(summaryMessage, systemMessage);
            }
            catch
            {
                if (this.FailOnError)
                {
                    throw;
                }
            }
        }

        return truncatedHistory;

        // Inner function to assemble the summarized history
        IEnumerable<ChatMessageContent> AssemblySummarizedHistory(ChatMessageContent? summaryMessage, ChatMessageContent? systemMessage)
        {
            if (systemMessage is not null)
            {
                yield return systemMessage;
            }

            if (insertionPoint > 0 && !this.UseSingleSummary)
            {
                for (int index = 0; index <= insertionPoint - 1; ++index)
                {
                    yield return chatHistory[index];
                }
            }

            if (summaryMessage is not null)
            {
                yield return summaryMessage;
            }

            for (int index = truncationIndex; index < chatHistory.Count; ++index)
            {
                yield return chatHistory[index];
            }
        }
    }

    /// <inheritdoc/>
    public override bool Equals(object? obj)
    {
        ChatHistorySummarizationReducer? other = obj as ChatHistorySummarizationReducer;
        return other != null &&
               this._thresholdCount == other._thresholdCount &&
               this._targetCount == other._targetCount &&
               this.UseSingleSummary == other.UseSingleSummary &&
               string.Equals(this.SummarizationInstructions, other.SummarizationInstructions, StringComparison.Ordinal);
    }

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(nameof(ChatHistorySummarizationReducer), this._thresholdCount, this._targetCount, this.SummarizationInstructions, this.UseSingleSummary);

    private readonly IChatCompletionService _service;
    private readonly int _thresholdCount;
    private readonly int _targetCount;
}
