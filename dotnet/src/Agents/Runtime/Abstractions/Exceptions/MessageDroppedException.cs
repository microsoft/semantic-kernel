// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Exception thrown when a message is dropped.
/// </summary>
[ExcludeFromCodeCoverage]
public class MessageDroppedException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MessageDroppedException"/> class.
    /// </summary>
    public MessageDroppedException() : base("The message was dropped.") { }

    /// <summary>
    /// Initializes a new instance of the <see cref="MessageDroppedException"/> class with a custom error message.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    public MessageDroppedException(string message) : base(message) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="MessageDroppedException"/> class with a custom error message and an inner exception.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    /// <param name="innerException">The inner exception that caused this error.</param>
    public MessageDroppedException(string message, Exception innerException) : base(message, innerException) { }
}
