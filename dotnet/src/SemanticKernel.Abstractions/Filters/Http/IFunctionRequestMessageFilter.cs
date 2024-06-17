// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel;

#pragma warning disable CA1716 // Identifiers should not match keywords (Func<FunctionRequestMessageContext, Task> next)

/// <summary>
/// Interface for filtering creation of <see cref="HttpRequestMessage"/> instances.
/// </summary>
[Experimental("SKEXP0001")]
public interface IFunctionRequestMessageFilter
{
    /// <summary>
    /// </summary>
    HttpRequestMessage CreateHttpRequestMessage(FunctionRequestMessageContext context, Func<FunctionRequestMessageContext, HttpRequestMessage> next);
}
