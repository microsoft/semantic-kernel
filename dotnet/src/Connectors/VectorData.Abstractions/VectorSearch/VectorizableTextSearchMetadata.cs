// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides metadata about an <see cref="IVectorizableTextSearch{TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public class VectorizableTextSearchMetadata
{
    /// <summary>The name of the vector store.</summary>
    /// <remarks>
    /// Where possible, this maps to the "db.system.name" attribute defined in the
    /// OpenTelemetry Semantic Conventions for database calls and systems, see <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
    /// Example: redis, sqlite, mysql.
    /// </remarks>
    public string? VectorStoreSystemName { get; init; }

    /// <summary>
    /// The name of the database.
    /// </summary>
    public string? DatabaseName { get; init; }

    /// <summary>
    /// The name of a collection (table, container) within the database.
    /// </summary>
    public string? CollectionName { get; init; }

    /// <summary>
    /// Initializes an instance of <see cref="VectorizableTextSearchMetadata"/> from <see cref="VectorStoreRecordCollectionMetadata"/>.
    /// </summary>
    /// <param name="collectionMetadata">Instance of <see cref="VectorStoreRecordCollectionMetadata"/>.</param>
    public static VectorizableTextSearchMetadata From(VectorStoreRecordCollectionMetadata collectionMetadata)
    {
        return new()
        {
            VectorStoreSystemName = collectionMetadata.VectorStoreSystemName,
            DatabaseName = collectionMetadata.DatabaseName,
            CollectionName = collectionMetadata.CollectionName
        };
    }
}
