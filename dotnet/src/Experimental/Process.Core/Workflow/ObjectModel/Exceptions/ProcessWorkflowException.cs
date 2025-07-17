// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process.Workflows;

/// <summary>
/// Represents any exception that occurs during the execution of a process workflow.
/// </summary>
public class ProcessWorkflowException : KernelException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessWorkflowException"/> class.
    /// </summary>
    public ProcessWorkflowException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessWorkflowException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public ProcessWorkflowException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ProcessWorkflowException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public ProcessWorkflowException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
