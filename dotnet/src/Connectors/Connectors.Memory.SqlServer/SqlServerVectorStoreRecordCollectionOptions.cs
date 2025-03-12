﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// Options when creating a <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class SqlServerVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets the database schema.
    /// </summary>
    public string? Schema { get; init; }

    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the SQL Server record.
    /// </summary>
    /// <remarks>
    /// If not set, the default mapper will be used.
    /// </remarks>
    public IVectorStoreRecordMapper<TRecord, IDictionary<string, object?>>? Mapper { get; init; }

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? RecordDefinition { get; init; }
}
