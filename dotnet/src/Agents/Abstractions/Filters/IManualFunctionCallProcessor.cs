// Copyright (c) Microsoft. All rights reserved.
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Filters;

/// <summary>
/// %%%
/// </summary>
public interface IManualFunctionCallProcessor
{
    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="context">The <see cref="ManualFunctionCallContext"/> containing the result of the function's invocation.</param>
    Task OnProcessFunctionCallAsync(ManualFunctionCallContext context);
}
