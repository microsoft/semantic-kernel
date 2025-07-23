// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process.Workflows;

/// <summary>
/// Represents an exception that occurs when building the process workflow.
/// </summary>
public class WorkflowBuilderException : ProcessWorkflowException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="WorkflowBuilderException"/> class.
    /// </summary>
    public WorkflowBuilderException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WorkflowBuilderException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public WorkflowBuilderException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="WorkflowBuilderException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public WorkflowBuilderException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
