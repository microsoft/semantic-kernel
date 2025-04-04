// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents a message type and source in the context of a kernel process.
/// </summary>
public class KernelProcessMessageSource
{
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
    public string MessageType { get; set; }

    /// <summary>
    /// The unique identifier of the step that generated this message.
    /// </summary>
    public string SourceStepId { get; set; }
}
