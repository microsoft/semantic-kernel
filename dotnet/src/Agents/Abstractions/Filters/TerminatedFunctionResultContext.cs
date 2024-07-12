// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// %%%
/// </summary>
public class TerminatedFunctionResultContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="TerminatedFunctionResultContext"/> class.
    /// </summary>
    /// <param name="functionResults"></param>
    internal TerminatedFunctionResultContext(IReadOnlyList<FunctionResultContent> functionResults)
    {
        this.FunctionResults = functionResults;
    }

    /// <summary>
    /// The <see cref="System.Threading.CancellationToken"/> to monitor for cancellation requests.
    /// The default is <see cref="CancellationToken.None"/>.
    /// </summary>
    public CancellationToken CancellationToken { get; init; }

    ///// <summary>
    ///// Gets the <see cref="Microsoft.SemanticKernel.Kernel"/> containing services, plugins, and other state for use throughout the operation.
    ///// </summary>
    //public Kernel Kernel { get; } // %%%

    /// <summary>
    /// Gets the <see cref="KernelFunction"/> with which this filter is associated.
    /// </summary>
    public IReadOnlyList<FunctionResultContent> FunctionResults { get; }

    /// <summary>
    /// %%%
    /// </summary>
    public IEnumerable<KernelContent>? TransformedContent { get; set; }
}
