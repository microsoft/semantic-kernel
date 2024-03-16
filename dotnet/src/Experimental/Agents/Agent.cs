// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Base class for agents.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="Agent"/> class.
/// </remarks>
public abstract class Agent
{
    /// <summary>
    /// The description of the agent (optional)
    /// </summary>
    public abstract string? Description { get; }

    /// <summary>
    /// The identifier of the agent (optional)
    /// </summary>
    public abstract string Id { get; }

    /// <summary>
    /// The name of the agent (optional)
    /// </summary>
    public abstract string? Name { get; }

    /// <summary>
    /// The type of channel associated with the agent, should one be required.
    /// </summary>
    /// <remarks>
    /// Each implementation of <see cref="Agent"/> must be associated
    /// with a corresponding <see cref="AgentChannel"/>.
    /// </remarks>
    protected internal abstract Type ChannelType { get; }

    /// <summary>
    /// Produce the an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="nexus">The <see cref="AgentNexus"/> requesting the channel.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    protected internal abstract Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken);
}
