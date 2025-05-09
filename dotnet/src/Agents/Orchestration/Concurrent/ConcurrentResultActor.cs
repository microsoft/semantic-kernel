// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// Actor for capturing each <see cref="ConcurrentMessages.Result"/> message.
/// </summary>
internal sealed class ConcurrentResultActor :
    OrchestrationActor,
    IHandle<ConcurrentMessages.Result>
{
    private readonly ConcurrentQueue<ConcurrentMessages.Result> _results;
    private readonly AgentType _orchestrationType;
    private readonly int _expectedCount;
    private int _resultCount;

    /// <summary>
    /// Initializes a new instance of the <see cref="ConcurrentResultActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="expectedCount">The expected number of messages to be received.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public ConcurrentResultActor(
        AgentId id,
        IAgentRuntime runtime,
        OrchestrationContext context,
        AgentType orchestrationType,
        int expectedCount,
        ILogger logger)
        : base(id, runtime, context, "Captures the results of the ConcurrentOrchestration", logger)
    {
        this._orchestrationType = orchestrationType;
        this._expectedCount = expectedCount;
        this._results = [];
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(ConcurrentMessages.Result item, MessageContext messageContext)
    {
        this.Logger.LogConcurrentResultCapture(this.Id, this._resultCount + 1, this._expectedCount);

        this._results.Enqueue(item);

        if (Interlocked.Increment(ref this._resultCount) == this._expectedCount)
        {
            await this.SendMessageAsync(this._results.ToArray(), this._orchestrationType, messageContext.CancellationToken).ConfigureAwait(false);
        }
    }
}
