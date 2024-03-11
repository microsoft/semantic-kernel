// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Interface for filtering actions during function invocation.
/// </summary>
[Experimental("SKEXP0001")]
public interface IFunctionFilter
{
    /// <summary>
    /// Method which is executed before function invocation.
    /// </summary>
    /// <param name="context">Data related to function before invocation.</param>
    void OnFunctionInvoking(FunctionInvokingContext context);

    /// <summary>
    /// Method which is executed after function invocation.
    /// </summary>
    /// <param name="context">Data related to function after invocation.</param>
    void OnFunctionInvoked(FunctionInvokedContext context);
}
