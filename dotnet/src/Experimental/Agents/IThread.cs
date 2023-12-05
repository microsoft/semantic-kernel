// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;

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
    Task<string> InvokeAsync(string userMessage);

    /// <summary>
    /// Gets the chat messages.
    /// </summary>
    IReadOnlyList<ChatMessageContent> ChatMessages { get; }
}
