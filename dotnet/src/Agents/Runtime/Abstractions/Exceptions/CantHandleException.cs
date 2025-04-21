// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Exception thrown when a handler cannot process the given message.
/// </summary>
[ExcludeFromCodeCoverage]
public class CantHandleException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="CantHandleException"/> class.
    /// </summary>
    public CantHandleException() : base("The handler cannot process the given message.") { }

    /// <summary>
    /// Initializes a new instance of the <see cref="CantHandleException"/> class with a custom error message.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    public CantHandleException(string message) : base(message) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="CantHandleException"/> class with a custom error message and an inner exception.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    /// <param name="innerException">The inner exception that caused this error.</param>
    public CantHandleException(string message, Exception innerException) : base(message, innerException) { }
}
