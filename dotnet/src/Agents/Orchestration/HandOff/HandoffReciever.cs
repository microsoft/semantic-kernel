// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// %%%
/// </summary>
/// <param name="result"></param>
internal delegate ValueTask HandoffResultHandlerAsync(HandoffMessages.Input result);

/// <summary>
/// A <see cref="ManagedAgent"/> built around a <see cref="Agent"/>.
/// </summary>
internal sealed class HandoffReciever : RuntimeAgent
{
    private readonly HandoffResultHandlerAsync _resultHandler;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentProxy"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="resultHandler">// %%%</param>
    public HandoffReciever(AgentId id, IAgentRuntime runtime, HandoffResultHandlerAsync resultHandler)
        : base(id, runtime, "// %%% DESCRIPTION")
    {
        this.RegisterHandler<HandoffMessages.Input>(this.OnHandoffAsync);
        this._resultHandler = resultHandler;
    }

    /// <summary>
    /// %%%
    /// </summary>
    public bool IsComplete => true; // %%% TODO

    /// <inheritdoc/>
    private ValueTask OnHandoffAsync(HandoffMessages.Input message, MessageContext context)
    {
        return this._resultHandler.Invoke(message);
    }
}
