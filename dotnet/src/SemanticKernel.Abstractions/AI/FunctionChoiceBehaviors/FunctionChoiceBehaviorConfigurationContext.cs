// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel;

/// <summary>
/// The context is to be provided by the choice behavior consumer – AI connector in order to obtain the choice behavior configuration.
/// </summary>
public sealed class FunctionChoiceBehaviorConfigurationContext
{
    /// <summary>
    /// Creates a new instance of <see cref="FunctionChoiceBehaviorConfigurationContext"/>.
    /// </summary>
    /// <param name="chatHistory">History of the current chat session.</param>
    public FunctionChoiceBehaviorConfigurationContext(ChatHistory chatHistory)
    {
        this.ChatHistory = chatHistory;
    }

    /// <summary>
    /// History of the current chat session.
    /// </summary>
    public ChatHistory ChatHistory { get; }

    /// <summary>
    /// The <see cref="Kernel"/> used by in the current chat session.
    /// </summary>
    public Kernel? Kernel { get; init; }

    /// <summary>
    /// Request sequence index of automatic function invocation process. Starts from 0.
    /// </summary>
    public int RequestSequenceIndex { get; init; }
}
