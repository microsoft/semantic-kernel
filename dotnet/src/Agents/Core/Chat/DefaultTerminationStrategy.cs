// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// The termination strategy attached to the default state of <see cref="AgentGroupChatSettings.TerminationStrategy"/> will
/// execute to <see cref="TerminationStrategy.MaximumIterations"/> without signaling termination.
/// </summary>
public sealed class DefaultTerminationStrategy : TerminationStrategy
{
    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(false);
    }
}
