// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a message type and source in the context of a kernel process.
/// </summary>
[DataContract]
public class KernelProcessMessageSource
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessMessageSource"/> class.
    /// </summary>
    /// <param name="messageType">The message type</param>
    /// <param name="sourceStepId">The unique Id of the source step.</param>
    public KernelProcessMessageSource(string messageType, string sourceStepId)
    {
        Verify.NotNullOrWhiteSpace(messageType, nameof(messageType));
        Verify.NotNullOrWhiteSpace(sourceStepId, nameof(sourceStepId));

        this.MessageType = messageType;
        this.SourceStepId = sourceStepId;
    }

    /// <summary>
    /// The type of message.
    /// </summary>
    [DataMember]
    public string MessageType { get; set; }

    /// <summary>
    /// The unique identifier of the step that generated this message.
    /// </summary>
    [DataMember]
    public string SourceStepId { get; set; }
}
