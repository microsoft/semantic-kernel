// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// %%%
/// </summary>
public class ChatHistorySummarizationReducer : IChatHistoryReducer
{
    private const string SummaryMetadataKey = "__summary__";

    private const string DefaultSummarizationPrompt =
        """
        Provide a concise and complete summarizion of the entire chat that does not exceed 5 sentences.

        Take care to to summarize both user and assistant interactions.

        Pay attention to the relevance and importance of the information, focusing on capturing the most significant aspects while maintaining the overall coherence of the summary. 

        The updated summary should serve to maintain continuity in the dialog and help you respond accurately to the user based on the information.

        Your response should only consist of the updated summary without explanation.;
        """;

    /// <summary>
    /// %%%
    /// </summary>
    public string SummarizationInstructions { get; init; } = DefaultSummarizationPrompt;

    /// <inheritdoc/>
    public override int GetHashCode() => HashCode.Combine(nameof(ChatHistorySummarizationReducer), this._thresholdCount, this._targetCount);

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="history"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        int insertionPoint = history.GetFinalSummaryIndex(SummaryMetadataKey);

        IReadOnlyList<ChatMessageContent> summarizedHistory = history.Extract(insertionPoint, this._targetCount).ToArray(); // %%% LOCATE INDEX

        ChatMessageContent summary = new(AuthorRole.User, "Summarized history", metadata: new Dictionary<string, object?>() { { SummaryMetadataKey, true } }); // %%% PERFORM SUMMARY

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (summary != null)
        {
            truncatedHistory = [.. history.Extract(0, insertionPoint), summary, .. history.Extract(this._targetCount)];
        }

        return Task.FromResult(truncatedHistory);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistorySummarizationReducer"/> class.
    /// </summary>
    /// <param name="kernel">%%%</param>
    /// <param name="targetCount">The desired number of target messages after reduction.</param>
    /// <param name="thresholdCount">An optional number of messages beyond the 'targetCount' that must be present in order to trigger reduction/</param>
    /// <remarks>
    /// While the 'thresholdCount' is optional, it is recommended to provided so that reduction is not triggered
    /// for every incremental addition to the chat history beyond the 'targetCount'.
    /// </remarks>>
    public ChatHistorySummarizationReducer(Kernel kernel, int targetCount, int? thresholdCount = null)
    {
        Verify.True(targetCount > 0, "Target message count must be greater than zero.");
        Verify.True(!thresholdCount.HasValue || thresholdCount > 0, "The reduction threshold length must be greater than zero.");

        this._targetCount = targetCount;

        this._thresholdCount = thresholdCount ?? 0;
    }

    private readonly int _thresholdCount;
    private readonly int _targetCount;
}
