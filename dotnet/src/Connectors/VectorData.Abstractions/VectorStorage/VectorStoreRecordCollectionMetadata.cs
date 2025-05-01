// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides metadata about an <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</summary>
public class VectorStoreRecordCollectionMetadata
{
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
    /// The name of a collection (table, container) within the vector store (database).
    /// </summary>
    public string? CollectionName { get; init; }
}
