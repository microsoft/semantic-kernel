// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Internal;

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="KernelAgent"/>
/// </summary>
public static class KernelAgentExtensions
{
    /// <summary>
    /// Render the provided instructions using the specified arguments.
    /// </summary>
    /// <param name="agent">A <see cref="KernelAgent"/>.</param>
    /// <param name="instructions">The instructions to format.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The rendered instructions</returns>
    public static Task<string?> FormatInstructionsAsync(this KernelAgent agent, string? instructions, CancellationToken cancellationToken = default)
    {
        return PromptRenderer.FormatInstructionsAsync(agent, instructions, cancellationToken);
    }
}
