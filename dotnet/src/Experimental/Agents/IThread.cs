// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Interface for a conversable thread.
/// </summary>
public interface IThread
{
    /// <summary>
    /// Add a message from the user to the thread.
    /// </summary>
    /// <param name="message">The user message.</param>
    /// <returns></returns>
    public void AddUserMessage(string message);

    /// <summary>
    /// Invokes the thread.
    /// </summary>
    /// <returns></returns>
    public Task<string> InvokeAsync();
}
