// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Context to be provided by function choice behavior in order to obtain the functions to be used by the AI model.
/// </summary>
public class FunctionChoiceBehaviorFunctionsSelectorContext
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionChoiceBehaviorFunctionsSelectorContext"/> class.
    /// </summary>
    /// <param name="chatHistory">The chat history.</param>
    public FunctionChoiceBehaviorFunctionsSelectorContext(ChatHistory chatHistory)
    {
        this.ChatHistory = chatHistory;
    }

    /// <summary>
    /// Functions to provide to AI model.
    /// </summary>
    public IReadOnlyList<KernelFunction>? Functions { get; init; }

    /// <summary>
    /// The <see cref="Kernel"/> to be used for function calling.
    /// </summary>
    public Kernel? Kernel { get; init; }

    /// <summary>
    /// The chat history.
    /// </summary>
    public ChatHistory ChatHistory { get; }
}
