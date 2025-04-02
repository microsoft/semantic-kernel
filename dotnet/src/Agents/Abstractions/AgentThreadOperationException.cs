// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Defines an exception that's thrown when an operation on an <see cref="AgentThread"/> fails, such as creating or deleting the thread.
/// </summary>
public class AgentThreadOperationException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AgentThreadOperationException"/> class.
    /// </summary>
    public AgentThreadOperationException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentThreadOperationException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public AgentThreadOperationException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentThreadOperationException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public AgentThreadOperationException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
