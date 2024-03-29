// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization bound to <see cref="LocalChannel"/>.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="LocalKernelAgent"/> class.
/// </remarks>
/// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
/// <param name="instructions">The agent instructions</param>
public abstract class LocalKernelAgent(Kernel kernel, string? instructions = null) : KernelAgent(kernel, instructions), ILocalAgent
{
    /// <inheritdoc/>
    protected internal override IEnumerable<string> GetChannelKeys()
    {
        yield return typeof(LocalChannel).FullName;
    }

    /// <inheritdoc/>
    protected internal sealed override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new LocalChannel());
    }

    /// <inheritdoc/>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        IEnumerable<ChatMessageContent> history,
        CancellationToken cancellationToken = default);
}
