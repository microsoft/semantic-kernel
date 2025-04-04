// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Builder class for defining conditions to listen for in a process.
/// </summary>
public class ListenForBuilder
{
    private readonly ProcessBuilder _processBuilder;

    /// <summary>
    /// Initializes a new instance of the <see cref="ListenForBuilder"/> class.
    /// </summary>
    /// <param name="processBuilder">The process builder.</param>
    public ListenForBuilder(ProcessBuilder processBuilder)
    {
        this._processBuilder = processBuilder;
    }

    /// <summary>
    /// Defines a message to listen for from a specific process step.
    /// </summary>
    /// <param name="messageType">The type of the message.</param>
    /// <param name="from">The process step from which the message originates.</param>
    /// <returns>A builder for defining the target of the message.</returns>
    public ListenForTargetBuilder Message(string messageType, ProcessStepBuilder from)
    {
        Verify.NotNullOrWhiteSpace(messageType, nameof(messageType));
        Verify.NotNull(from, nameof(from));

        return new ListenForTargetBuilder(new List<MessageSourceBuilder> { new(messageType, from) }, this._processBuilder);
    }

    /// <summary>
    /// Defines a condition to listen for all of the specified message sources.
    /// </summary>
    /// <param name="messageSources">The list of message sources.</param>
    /// <returns>A builder for defining the target of the messages.</returns>
    public ListenForTargetBuilder AllOf(List<MessageSourceBuilder> messageSources)
    {
        Verify.NotNullOrEmpty(messageSources, nameof(messageSources));
        return new ListenForTargetBuilder(messageSources, this._processBuilder);
    }
}
