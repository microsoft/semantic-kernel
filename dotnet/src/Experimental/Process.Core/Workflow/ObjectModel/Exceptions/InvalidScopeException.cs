// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Process.Workflows;

/// <summary>
/// Represents an exception that occurs when the specific scope is invalid.
/// </summary>
public sealed class InvalidScopeException : ProcessWorkflowException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="InvalidScopeException"/> class.
    /// </summary>
    public InvalidScopeException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="InvalidScopeException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public InvalidScopeException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="InvalidScopeException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public InvalidScopeException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
