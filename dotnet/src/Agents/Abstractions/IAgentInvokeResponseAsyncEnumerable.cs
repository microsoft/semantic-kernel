// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Represents a response from an agent invocation.
/// </summary>
/// <typeparam name="T">The type of data returned by the response.</typeparam>
public interface IAgentInvokeResponseAsyncEnumerable<out T> : IAsyncEnumerable<T>
{
    /// <summary>
    /// Gets the thread associated with this response.
    /// </summary>
    AgentThread Thread { get; }
}
