// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Base exception type thrown for any type of failure when using vector stores.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class VectorStoreException : KernelException
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreException"/> class.
    /// </summary>
    protected VectorStoreException()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreException"/> class with a specified error message.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    protected VectorStoreException(string? message) : base(message)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreException"/> class with a specified error message and a reference to the inner exception that is the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that is the cause of the current exception, or a null reference if no inner exception is specified.</param>
    protected VectorStoreException(string? message, Exception? innerException) : base(message, innerException)
    {
    }

    /// <summary>
    /// Gets or sets the name of the database system that the failing operation was performed on.
    /// </summary>
    public string? DBSystem { get; init; }

    /// <summary>
    /// Gets or sets the name of the database collection that the failing operation was performed on.
    /// </summary>
    public string? DBCollectionName { get; init; }

    /// <summary>
    /// Gets or sets the name of the database operation that failed.
    /// </summary>
    public string? DBOperationName { get; init; }
}
