// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base abstraction for all Semantic Kernel agents.  An agent instance
/// may participate in one or more conversations, or <see cref="AgentNexus"/>.
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
    /// Set of keys to establish channel affinity.  Minimum expected key-set:
    /// <example>
    /// yield return typeof(YourAgentChannel).FullName;
    /// </example>
    /// </summary>
    /// <remarks>
    /// Any specific agent type may need to manage multiple channels.  For example, an
    /// agents targeting two different Azure OpenAI endpoints each require their own channel.
    /// In this case, the endpoint would be expressed as an additional key.
    /// </remarks>
    protected internal abstract IEnumerable<string> GetChannelKeys();

    /// <summary>
    /// Produce the an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    /// <remarks>
    /// Every agent conversation, or <see cref="AgentNexus"/>, will establish one or more <see cref="AgentChannel"/>
    /// objects according to the specific <see cref="Agent"/> type.
    /// </remarks>
    protected internal abstract Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken);
}
