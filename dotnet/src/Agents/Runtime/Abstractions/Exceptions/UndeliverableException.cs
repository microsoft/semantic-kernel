// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Exception thrown when a message cannot be delivered.
/// </summary>
[ExcludeFromCodeCoverage]
public class UndeliverableException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="UndeliverableException"/> class.
    /// </summary>
    public UndeliverableException() : base("The message cannot be delivered.") { }

    /// <summary>
    /// Initializes a new instance of the <see cref="UndeliverableException"/> class with a custom error message.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    public UndeliverableException(string message) : base(message) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="UndeliverableException"/> class with a custom error message and an inner exception.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    /// <param name="innerException">The inner exception that caused this error.</param>
    public UndeliverableException(string message, Exception innerException) : base(message, innerException) { }
}
