// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

#pragma warning disable CA1716 // Identifiers should not match keywords (Func<FunctionCallInvocationContext, Task> next)

/// <summary>
/// Interface for filtering actions during function calling invocation.
/// </summary>
[Experimental("SKEXP0001")]
public interface IFunctionCallFilter
{
    /// <summary>
    /// Method which is called asynchronously before function calling.
    /// </summary>
    /// <param name="context">Instance of <see cref="FunctionCallInvocationContext"/> with function calling details.</param>
    /// <param name="next">Delegate to the next filter in pipeline or function calling itself. If it's not invoked, next filter won't be invoked and function calling will be stopped.</param>
    Task OnFunctionCallInvocationAsync(FunctionCallInvocationContext context, Func<FunctionCallInvocationContext, Task> next);
}
