// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides metadata about an <see cref="VectorStoreCollection{TKey, TRecord}"/>.</summary>
public class VectorStoreCollectionMetadata
{
    /// <summary>Gets or sets the name of the vector store system.</summary>
    /// <remarks>
    /// Where possible, this value maps to the "db.system.name" attribute defined in the
    /// OpenTelemetry Semantic Conventions for database calls and systems; see <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
    /// Example: redis, sqlite, mysql.
    /// </remarks>
    public string? VectorStoreSystemName { get; init; }

    /// <summary>
    /// Gets or sets the name of the vector store (database).
    /// </summary>
    public string? VectorStoreName { get; init; }

    /// <summary>
    /// Gets or sets the name of a collection (table, container) within the vector store (database).
    /// </summary>
    public string? CollectionName { get; init; }
}
