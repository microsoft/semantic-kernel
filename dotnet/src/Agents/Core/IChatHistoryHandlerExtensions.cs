// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Contract for an agent that utilizes a <see cref="ChatHistoryChannel"/>.
/// </summary>
public static class IChatHistoryHandlerExtensions
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="history"></param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public static Task<(bool isReduced, ChatHistory history)> ReduceAsync(this IChatHistoryHandler agent, ChatHistory history, CancellationToken cancellationToken = default) =>
        history.ReduceAsync(agent.HistoryReducer, cancellationToken);
}
