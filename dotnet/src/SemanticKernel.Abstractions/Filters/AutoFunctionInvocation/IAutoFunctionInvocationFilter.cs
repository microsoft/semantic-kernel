// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

#pragma warning disable CA1716 // Identifiers should not match keywords (Func<FunctionCallInvocationContext, Task> next)

/// <summary>
/// Interface for filtering actions during automatic function invocation.
/// </summary>
public interface IAutoFunctionInvocationFilter
{
    /// <summary>
    /// Method which is called asynchronously before automatic function invocation.
    /// </summary>
    /// <param name="context">Instance of <see cref="AutoFunctionInvocationContext"/> with automatic function invocation details.</param>
    /// <param name="next">Delegate to the next filter in pipeline or function invocation itself. If it's not invoked, next filter won't be invoked and function invocation will be skipped.</param>
    Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next);
}
