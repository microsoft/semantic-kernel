// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// %%%
/// </summary>
/// <param name="result"></param>
internal delegate void BroadcastResultHandler(BroadcastMessages.Result result);

/// <summary>
/// A <see cref="ManagedAgent"/> built around a <see cref="Agent"/>.
/// </summary>
internal sealed class BroadcastReciever : RuntimeAgent
{
    private readonly BroadcastResultHandler _resultHandler;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentProxy"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="resultHandler">// %%%</param>
    public BroadcastReciever(AgentId id, IAgentRuntime runtime, BroadcastResultHandler resultHandler)
        : base(id, runtime, "// %%% DESCRIPTION")
    {
        this.RegisterHandler<BroadcastMessages.Result>(this.OnResultAsync);
        this._resultHandler = resultHandler;
    }

    /// <summary>
    /// %%%
    /// </summary>
    public bool IsComplete => true; // %%% TODO

    /// <inheritdoc/>
    private ValueTask OnResultAsync(BroadcastMessages.Result message, MessageContext context)
    {
        this._resultHandler.Invoke(message);

        return ValueTask.CompletedTask;
    }
}
