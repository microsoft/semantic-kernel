// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process.Workflows;

/// <summary>
/// Represents an exception that occurs during the execution of a process action.
/// </summary>
public class ProcessActionException : ProcessWorkflowException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessActionException"/> class.
    /// </summary>
    public ProcessActionException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessActionException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public ProcessActionException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessActionException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public ProcessActionException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
