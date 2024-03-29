// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Agents.Filters;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// $$$
/// </summary>
public static  class KernelAgentExtensions
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static Task<string?> FormatInstructionsAsync(this KernelAgent agent, CancellationToken cancellationToken = default)
    {
        return PromptRenderer.FormatInstructionsAsync(agent, cancellationToken);
    }
}
