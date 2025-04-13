// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// %%% COMMENT
/// </summary>
internal sealed class BroadcastResultActor : BaseAgent,
    IHandle<BroadcastMessages.Result>
{
    private readonly ConcurrentQueue<BroadcastMessages.Result> _results;
    private readonly AgentType _orchestrationType;
    private readonly int _expectedCount;
    private int _resultCount;

    /// <summary>
    /// Initializes a new instance of the <see cref="BroadcastResultActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="orchestrationType">Identifies the orchestration agent.</param>
    /// <param name="expectedCount">The expected number of messages to be recieved.</param>
    public BroadcastResultActor(
        AgentId id,
        IAgentRuntime runtime,
        AgentType orchestrationType,
        int expectedCount)
        : base(id, runtime, "Captures the results of the BroadcastOrchestration")
    {
        this._orchestrationType = orchestrationType;
        this._expectedCount = expectedCount;
        this._results = [];
    }

    /// <inheritdoc/>
    public async ValueTask HandleAsync(BroadcastMessages.Result item, MessageContext messageContext)
    {
        Trace.WriteLine($"> BROADCAST RESULT: {this.Id.Type} (#{this._resultCount + 1})");

        this._results.Enqueue(item);

        if (Interlocked.Increment(ref this._resultCount) == this._expectedCount)
        {
            await this.SendMessageAsync(this._results.ToArray(), new AgentId(this._orchestrationType, AgentId.DefaultKey)).ConfigureAwait(false); // %%% AGENTID
        }
    }
}
