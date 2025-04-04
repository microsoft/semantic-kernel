// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// %%% TODO: Justify
/// </summary>
public abstract class ServiceAgent : Agent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ServiceAgent"/> class.
    /// </summary>
    protected ServiceAgent()
    {
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        throw new NotSupportedException();
        //return this._agent.CreateChannelAsync(cancellationToken);
    }

    /// <inheritdoc/>
    protected override IEnumerable<string> GetChannelKeys()
    {
        throw new NotSupportedException();
        //return this._agent.GetChannelKeys();
    }

    /// <inheritdoc/>
    protected override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
    {
        throw new NotSupportedException();
        //return this._agent.RestoreChannelAsync(channelState, cancellationToken);
    }
}
