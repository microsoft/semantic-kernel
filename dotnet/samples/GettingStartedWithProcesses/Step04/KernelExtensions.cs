// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Step04;

/// <summary>
/// Convenience extensions for agent based process patterns.
/// </summary>
internal static class KernelExtensions
{
    /// <summary>
    /// Return chat history from a singleton <see cref="IChatHistoryProvider"/>.
    /// </summary>
    public static IChatHistoryProvider GetHistory(this Kernel kernel) =>
        kernel.Services.GetRequiredService<IChatHistoryProvider>();

    /// <summary>
    /// Access an agent as a keyed service.
    /// </summary>
    public static TAgent GetAgent<TAgent>(this Kernel kernel, string key) where TAgent : Agent =>
        kernel.Services.GetRequiredKeyedService<TAgent>(key);

    /// <summary>
    /// Summarize chat history using reducer accessed as a keyed service.
    /// </summary>
    public static async Task<string> SummarizeHistoryAsync(this Kernel kernel, string key, IReadOnlyList<ChatMessageContent> history)
    {
        ChatHistorySummarizationReducer reducer = kernel.Services.GetRequiredKeyedService<ChatHistorySummarizationReducer>(key);
        IEnumerable<ChatMessageContent>? reducedResponse = await reducer.ReduceAsync(history);
        ChatMessageContent summary = reducedResponse?.First() ?? throw new InvalidDataException("No summary available");
        return summary.ToString();
    }
}
