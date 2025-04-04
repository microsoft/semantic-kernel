// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a builder for defining the source of a message in a process.
/// </summary>
public class MessageSourceBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MessageSourceBuilder"/> class.
    /// </summary>
    /// <param name="messageType">The meassage type</param>
    /// <param name="source">The source step builer</param>
    public MessageSourceBuilder(string messageType, ProcessStepBuilder source)
    {
        this.MessageType = messageType;
        this.Source = source;
    }

    /// <summary>
    /// The message type
    /// </summary>
    public string MessageType { get; }

    /// <summary>
    /// The source step builder.
    /// </summary>
    public ProcessStepBuilder Source { get; }
}
