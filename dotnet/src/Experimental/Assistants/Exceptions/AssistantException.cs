// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Exceptions;

/// <summary>
/// Assistant specific <see cref="KernelException"/>.
/// </summary>
public class AssistantException : KernelException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AssistantException"/> class.
    /// </summary>
    public AssistantException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AssistantException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public AssistantException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AssistantException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public AssistantException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
