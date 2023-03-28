// Copyright (c) Microsoft. All rights reserved.

using System;

namespace RestSkillsApi;

/// <summary>
/// Exception to be throw if rest operation has failed. E.g. mandatory property is missing or empty, value is out of range
/// </summary>
public class RestOperationException : Exception
{
    /// <summary>
    /// Creates an instance of a <see cref="RestOperationException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    internal RestOperationException(string message) : base(message)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="RestOperationException"/> class.
    /// </summary>
    /// <param name="message">The exception message.</param>
    /// <param name="innerException">The inner exception.</param>
    internal RestOperationException(string message, Exception innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Creates an instance of a <see cref="RestOperationException"/> class.
    /// </summary>
    internal RestOperationException()
    {
    }
}
