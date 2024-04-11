// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// The termination strategy attached to the default state of <see cref="ChatExecutionSettings.TerminationStrategy"/>.
/// Terminates immediate, by default.  Behavior can be overriden via <see cref="DefaultTerminationStrategy.DisableTermination"/>.
/// </summary>
public sealed class DefaultTerminationStrategy : TerminationStrategy
{
    /// <summary>
    /// Strategy terminates by default, but may be overridden by setting this property.
    /// The <see cref="TerminationStrategy.MaximumIterations"/> property provides additional
    /// control to this strategy.
    /// </summary>
    public bool DisableTermination { get; set; }

    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        bool shouldTerminate = !this.DisableTermination;

        return Task.FromResult(!this.DisableTermination);
    }
}
