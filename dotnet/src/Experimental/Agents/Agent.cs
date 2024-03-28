// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
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
    /// Set of keys for tracking channel affinity.
    /// </summary>
    protected internal abstract IEnumerable<string> GetChannelKeys();

    /// <summary>
    /// Produce the an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    protected internal abstract Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken);
}
