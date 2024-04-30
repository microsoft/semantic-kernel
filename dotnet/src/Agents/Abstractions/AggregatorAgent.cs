// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines the relationship between the internal aggregated chat and the chat
/// with which <see cref="AggregatorAgent"/> is participating.
/// </summary>
public enum AggregatorMode
{
    /// <summary>
    /// A flat embedding of the aggregated chat within another chat.
    /// </summary>
    Flat,

    /// <summary>
    /// A nested embedding the aggregated chat within another chat.
    /// </summary>
    Nested,
}

/// <summary>
/// Allows an <see cref="AgentChat"/> to participate in another <see cref="AgentChat"/> as an <see cref="Agent"/>.
/// </summary>
/// <param name="chatProvider">A factory method that produces a new <see cref="AgentChat"/> instance.</param>
public sealed class AggregatorAgent(Func<AgentChat> chatProvider) : Agent
{
    /// <summary>
    /// Defines the relationship between the internal aggregated chat and the chat
    /// with which <see cref="AggregatorAgent"/> is participating.
    /// Default: <see cref="AggregatorMode.Flat"/>.
    /// </summary>
    public AggregatorMode Mode { get; init; } = AggregatorMode.Flat;

    /// <inheritdoc/>
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(AggregatorChannel).FullName;
    }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new AggregatorChannel(chatProvider.Invoke()));
    }
}
