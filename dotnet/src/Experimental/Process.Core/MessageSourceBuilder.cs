// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

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
    /// <param name="source">The source step builder</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    public MessageSourceBuilder(string messageType, ProcessStepBuilder source, KernelProcessEdgeCondition? condition = null)
    {
        this.MessageType = messageType;
        this.Source = source;
        this.Condition = condition ?? new KernelProcessEdgeCondition((_, _) => Task.FromResult(true));
    }

    /// <summary>
    /// The message type
    /// </summary>
    public string MessageType { get; }

    /// <summary>
    /// The source step builder.
    /// </summary>
    public ProcessStepBuilder Source { get; }

    /// <summary>
    /// The condition that must be met for the message to be processed.
    /// </summary>
    public KernelProcessEdgeCondition Condition { get; }
}

public sealed class TypedMessageSourceBuilder<T> : MessageSourceBuilder
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MessageSourceBuilder{T}"/> class.
    /// </summary>
    /// <param name="source">The source step builder</param>
    /// <param name="condition">Condition that must be met for the message to be processed</param>
    public TypedMessageSourceBuilder(KernelProcessEventDescriptor<T> messageType, ProcessStepBuilder source, KernelProcessEdgeCondition? condition = null)
        : base(messageType.EventName, source, condition)
    {
        this.MessageDescriptor = messageType;
    }

    public KernelProcessEventDescriptor<T> MessageDescriptor { get; }
}
