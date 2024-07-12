// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// %%%
/// </summary>
public interface ITerminatedFunctionResultProcessor
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="context">The <see cref="TerminatedFunctionResultContext"/> containing the result of the terminated function.</param>
    Task OnProcessTerminatedFunctionResultAsync(TerminatedFunctionResultContext context);
}
