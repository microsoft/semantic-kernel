// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base abstraction for all Semantic Kernel agents.  An agent instance
/// may participate in one or more conversations, or <see cref="AgentChat"/>.
/// A conversation may include one or more agents.
/// </summary>
/// <remarks>
/// In addition to identity and descriptive meta-data, an <see cref="Agent"/>
/// must define its communication protocol, or <see cref="AgentChannel"/>.
/// </remarks>
public abstract class Agent
{
    /// <summary>
    /// Gets the description of the agent (optional).
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// Gets the identifier of the agent (optional).
    /// </summary>
    /// <value>
    /// The identifier of the agent. The default is a random GUID value, but that can be overridden.
    /// </value>
    public string Id { get; init; } = Guid.NewGuid().ToString();

    /// <summary>
    /// Gets the name of the agent (optional).
    /// </summary>
    public string? Name { get; init; }

    /// <summary>
    /// A <see cref="ILoggerFactory"/> for this <see cref="Agent"/>.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }

    /// <summary>
    /// The <see cref="ILogger"/> associated with this  <see cref="Agent"/>.
    /// </summary>
    protected ILogger Logger => this._logger ??= this.ActiveLoggerFactory.CreateLogger(this.GetType());

    /// <summary>
    /// Get the active logger factory, if defined; otherwise, provide the default.
    /// </summary>
    protected virtual ILoggerFactory ActiveLoggerFactory => this.LoggerFactory ?? NullLoggerFactory.Instance;

    /// <summary>
    /// Set of keys to establish channel affinity.  Minimum expected key-set:
    /// <example>
    /// yield return typeof(YourAgentChannel).FullName;
    /// </example>
    /// </summary>
    /// <remarks>
    /// Two specific agents of the same type may each require their own channel.  This is
    /// why the channel type alone is insufficient.
    /// For example, two OpenAI Assistant agents each targeting a different Azure OpenAI endpoint
    /// would require their own channel. In this case, the endpoint could be expressed as an additional key.
    /// </remarks>
    [Experimental("SKEXP0110")]
#pragma warning disable CA1024 // Use properties where appropriate
    protected internal abstract IEnumerable<string> GetChannelKeys();
#pragma warning restore CA1024 // Use properties where appropriate

    /// <summary>
    /// Produce an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    /// <remarks>
    /// Every agent conversation, or <see cref="AgentChat"/>, will establish one or more <see cref="AgentChannel"/>
    /// objects according to the specific <see cref="Agent"/> type.
    /// </remarks>
    [Experimental("SKEXP0110")]
    protected internal abstract Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken);

    /// <summary>
    /// Produce an <see cref="AgentChannel"/> appropriate for the agent type based on the provided state.
    /// </summary>
    /// <param name="channelState">The channel state, as serialized</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    /// <remarks>
    /// Every agent conversation, or <see cref="AgentChat"/>, will establish one or more <see cref="AgentChannel"/>
    /// objects according to the specific <see cref="Agent"/> type.
    /// </remarks>
    [Experimental("SKEXP0110")]
    protected internal abstract Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken);

    private ILogger? _logger;
}
