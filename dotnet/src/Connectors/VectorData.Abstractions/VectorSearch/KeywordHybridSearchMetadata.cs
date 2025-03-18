// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides metadata about an <see cref="IKeywordHybridSearch{TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public class KeywordHybridSearchMetadata
{
    /// <summary>The name of the vector store.</summary>
    /// <remarks>
    /// Where possible, this maps to the appropriate name defined in the
    /// OpenTelemetry Semantic Conventions for database calls and systems.
    /// <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
    /// </remarks>
    public string? VectorStoreName { get; init; }

    /// <summary>
    /// The name of the database.
    /// </summary>
    public string? DatabaseName { get; init; }

    /// <summary>
    /// The name of a collection (table, container) within the database.
    /// </summary>
    public string? CollectionName { get; init; }
}
