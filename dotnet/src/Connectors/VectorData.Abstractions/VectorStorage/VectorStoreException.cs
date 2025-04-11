// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a base exception type for any type of failure when using vector stores.
/// </summary>
public abstract class VectorStoreException : Exception
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
    /// Initializes a new instance of the <see cref="VectorStoreException"/> class with a specified error message and a reference to the inner exception that's the cause of this exception.
    /// </summary>
    /// <param name="message">The error message that explains the reason for the exception.</param>
    /// <param name="innerException">The exception that's the cause of the current exception, or a null reference if no inner exception is specified.</param>
    protected VectorStoreException(string? message, Exception? innerException) : base(message, innerException)
    {
    }

    /// <summary>The name of the vector store system.</summary>
    /// <remarks>
    /// Where possible, this maps to the "db.system.name" attribute defined in the
    /// OpenTelemetry Semantic Conventions for database calls and systems, see <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
    /// Example: redis, sqlite, mysql.
    /// </remarks>
    public string? VectorStoreSystemName { get; init; }

    /// <summary>
    /// The name of the vector store (database).
    /// </summary>
    public string? VectorStoreName { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector store collection that the failing operation was performed on.
    /// </summary>
    public string? CollectionName { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector store operation that failed.
    /// </summary>
    public string? OperationName { get; init; }
}
