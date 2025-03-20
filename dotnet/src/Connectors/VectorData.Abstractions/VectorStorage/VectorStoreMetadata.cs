// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides metadata about an <see cref="IVectorStore"/>.</summary>
[Experimental("SKEXP0020")]
public class VectorStoreMetadata
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
}
