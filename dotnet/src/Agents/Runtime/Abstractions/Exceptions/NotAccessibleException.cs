// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Runtime;

/// <summary>
/// Exception thrown when an attempt is made to access an unavailable value, such as a remote resource.
/// </summary>
[ExcludeFromCodeCoverage]
public class NotAccessibleException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="NotAccessibleException"/> class.
    /// </summary>
    public NotAccessibleException() : base("The requested value is not accessible.") { }

    /// <summary>
    /// Initializes a new instance of the <see cref="NotAccessibleException"/> class with a custom error message.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    public NotAccessibleException(string message) : base(message) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="NotAccessibleException"/> class with a custom error message and an inner exception.
    /// </summary>
    /// <param name="message">The custom error message.</param>
    /// <param name="innerException">The inner exception that caused this error.</param>
    public NotAccessibleException(string message, Exception innerException) : base(message, innerException) { }
}
