// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

#pragma warning disable CA1716 // Identifiers should not match keywords (Func<FunctionInvocationContext, Task> next)

/// <summary>
/// Interface for filtering actions during function invocation.
/// </summary>
public interface IFunctionInvocationFilter
{
    /// <summary>
    /// Method which is called asynchronously before function invocation.
    /// </summary>
    /// <param name="context">Instance of <see cref="FunctionInvocationContext"/> with function invocation details.</param>
    /// <param name="next">Delegate to the next filter in pipeline or function itself. If it's not invoked, next filter or function won't be invoked.</param>
    Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next);
}
