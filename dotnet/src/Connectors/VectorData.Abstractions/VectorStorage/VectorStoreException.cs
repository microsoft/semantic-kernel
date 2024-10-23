// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Base exception type thrown for any type of failure when using vector stores.
/// </summary>
public abstract class VectorStoreTestException : Exception
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreTestException"/> class.
    /// </summary>
    protected VectorStoreTestException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreTestException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    protected VectorStoreTestException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreTestException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    protected VectorStoreTestException(string? message, Exception? innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Gets or sets the type of vector store that the failing operation was performed on.
    /// </summary>
    public string? VectorStoreType { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector store collection that the failing operation was performed on.
    /// </summary>
    public string? CollectionName { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector store operation that failed.
    /// </summary>
    public string? OperationName { get; init; }
}
