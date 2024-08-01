// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

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
        Provide a concise and complete summarizion of the entire dialog that does not exceed 5 sentences..

        This summary should always:
        - Serve to maintain continuity in the dialog for the purpose of further dialog.
        - Summarize both user and assistant interactions with fidelity
        - Pay attention to the relevance and importance of the information, focusing on capturing the most significant aspects.

        This summary should never:
        - Critique, correct, interpret, presume, or assume.
        - Identify faults or correctness.
        - Analyze what has not occurred.
        """;

    /// <summary>
    /// System instructions for summarization.  Defaults to <see cref="DefaultSummarizationPrompt"/>.
    /// </summary>
    public string SummarizationInstructions { get; init; } = DefaultSummarizationPrompt;

    /// <summary>
    /// Flag to indicate if an exception should be thrown if summarization fails.
    /// </summary>
    public bool FailOnError { get; init; } = true;

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(nameof(ChatHistorySummarizationReducer), this._thresholdCount, this._targetCount);

    /// <inheritdoc/>
    public async Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Identify where summary messages end and regular history begins
        int insertionPoint = history.LocateSummarizationBoundary(SummaryMetadataKey);

        // First pass to determine the truncation index
        int truncationIndex = history.LocateSafeReductionIndex(this._targetCount, this._thresholdCount);

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (truncationIndex > 0)
        {
            // Second pass to extract history for summarization
            IReadOnlyList<ChatMessageContent> summarizedHistory = history.Extract(insertionPoint, truncationIndex).ToArray();

            try
            {
                // Summarize
                ChatHistory summarizationRequest = [.. summarizedHistory, new ChatMessageContent(AuthorRole.System, this.SummarizationInstructions)];
                ChatMessageContent summary = await this._service.GetChatMessageContentAsync(summarizationRequest, cancellationToken: cancellationToken).ConfigureAwait(false);
                summary.Metadata = new Dictionary<string, object?> { { SummaryMetadataKey, true } };

                // Assembly the summarized history
                if (insertionPoint > 0)
                {
                    truncatedHistory = [.. history.Extract(0, insertionPoint - 1), summary, .. history.Extract(truncationIndex)];
                }
                else
                {
                    truncatedHistory = [summary, .. history.Extract(truncationIndex)];
                }
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
    }

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

    private readonly IChatCompletionService _service;
    private readonly int _thresholdCount;
    private readonly int _targetCount;
}
