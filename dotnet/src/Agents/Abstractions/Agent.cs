// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

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
    /// The description of the agent (optional)
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// The identifier of the agent (optional).
    /// </summary>
    /// <reamarks>
    /// Default to a random guid value, but may be overridden.
    /// </reamarks>
    public string Id { get; init; } = Guid.NewGuid().ToString();

    /// <summary>
    /// The name of the agent (optional)
    /// </summary>
    public string? Name { get; init; }

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
    protected internal abstract IEnumerable<string> GetChannelKeys();

    /// <summary>
    /// Produce the an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    /// <remarks>
    /// Every agent conversation, or <see cref="AgentChat"/>, will establish one or more <see cref="AgentChannel"/>
    /// objects according to the specific <see cref="Agent"/> type.
    /// </remarks>
    protected internal abstract Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken);
}
