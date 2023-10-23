// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Represents the base exception from which all Semantic Kernel exceptions derive.
/// </summary>
public class SKException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SKException"/> class.
    /// </summary>
    public SKException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    public SKException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    public SKException(string? message, Exception? innerException) : base(message, innerException)
    {
    }
}
