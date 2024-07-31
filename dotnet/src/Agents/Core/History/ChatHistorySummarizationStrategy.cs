// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.History;

/// <summary>
/// %%%
/// </summary>
public class ChatHistorySummarizationStrategy : IChatHistoryReducer
{
    private const string SummaryMetadataKey = "__summary__";

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="history"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        int insertionPoint = this.LocateSummaryInsertionPoint(history);

        IReadOnlyList<ChatMessageContent> summarizedHistory = this.ExtractHistoryForSummarization(history, insertionPoint, this._targetCount).ToArray();

        ChatMessageContent summary = new(AuthorRole.User, "Summarized history", metadata: new Dictionary<string, object?>() { { SummaryMetadataKey, true } }); // %%% PERFORM SUMMARY

        IEnumerable<ChatMessageContent>? truncatedHistory = null;

        if (summary != null)
        {
            truncatedHistory = this.AssembleHistory(history, summary, insertionPoint, this._targetCount);
        }

        return Task.FromResult(truncatedHistory);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatHistorySummarizationStrategy"/> class.
    /// </summary>
    /// <param name="kernel">%%%</param>
    /// <param name="targetCount">The desired number of target messages after reduction.</param>
    /// <param name="thresholdCount">An optional number of messages beyond the 'targetCount' that must be present in order to trigger reduction/</param>
    /// <remarks>
    /// While the 'thresholdCount' is optional, it is recommended to provided so that reduction is not triggered
    /// for every incremental addition to the chat history beyond the 'targetCount'.
    /// </remarks>>
    public ChatHistorySummarizationStrategy(Kernel kernel, int targetCount, int? thresholdCount = null)
    {
        Verify.True(targetCount > 0, "Target message count must be greater than zero.");
        Verify.True(!thresholdCount.HasValue || thresholdCount > 0, "The reduction threshold length must be greater than zero.");

        this._targetCount = targetCount;

        this._thresholdCount = thresholdCount ?? 0;
    }

    private IEnumerable<ChatMessageContent> ExtractHistoryForSummarization(IReadOnlyList<ChatMessageContent> history, int insertionPoint, int truncationIndex)
    {
        for (int index = insertionPoint; index < truncationIndex; ++index)
        {
            yield return history[index];
        }
    }

    private IEnumerable<ChatMessageContent> AssembleHistory(IReadOnlyList<ChatMessageContent> history, ChatMessageContent summary, int insertionPoint, int truncationIndex)
    {
        for (int index = 0; index < insertionPoint; ++index)
        {
            yield return history[index];
        }

        yield return summary;

        for (int index = truncationIndex; index < history.Count; ++index)
        {
            yield return history[index];
        }
    }

    private int LocateSummaryInsertionPoint(IReadOnlyList<ChatMessageContent> history)
    {
        for (int index = 0; index < history.Count; ++index)
        {
            ChatMessageContent message = history[index];

            if (!message.Metadata?.ContainsKey(SummaryMetadataKey) ?? false)
            {
                return index;
            }
        }

        return 0;
    }

    private readonly int _thresholdCount;
    private readonly int _targetCount;
}
