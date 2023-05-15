// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// Exception to be throw if a REST API operation has failed. E.g. mandatory property is missing or empty, value is out of range
/// </summary>
public class RestApiOperationException : Exception
{
    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    internal RestApiOperationException(string message) : base(message)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception.</param>
    internal RestApiOperationException(string message, Exception innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOperationException"/> class.
    /// </summary>
    internal RestApiOperationException()
    {
    }
}
