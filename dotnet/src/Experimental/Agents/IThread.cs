// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Interface for a conversable thread.
/// </summary>
public interface IThread
{
    /// <summary>
    /// Invokes the thread.
    /// </summary>
    /// <returns></returns>
    public Task<string> InvokeAsync(string userMessage);
}
