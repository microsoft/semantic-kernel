// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Context containing information to be used by the functions selector.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionChoiceBehaviorFunctionsSelectorContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionChoiceBehaviorFunctionsSelectorContext"/> class.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    internal FunctionChoiceBehaviorFunctionsSelectorContext(ChatHistory chatHistory)
    {
        this.ChatHistory = chatHistory;
    }

    /// <summary>
    /// Functions to provide to AI model.
    /// </summary>
    public IReadOnlyList<KernelFunction>? Functions { get; init; }

    /// <summary>
    /// The chat history.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// The <see cref="Kernel"/>.
    /// </summary>
    public Kernel? Kernel { get; init; }

    /// <summary>
    /// Request sequence index of automatic function invocation process. Starts from 0.
    /// </summary>
    public int RequestSequenceIndex { get; init; }
}
