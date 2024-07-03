// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Options when creating a <see cref="RedisVectorRecordStore{TRecord}"/>.
/// </summary>
public sealed class RedisVectorRecordStoreOptions<TRecord>
    where TRecord : class
{
    /// <summary>
    /// Gets or sets the default collection name to use.
    /// If not provided here, the collection name will need to be provided for each operation or the operation will throw.
    /// </summary>
    public string? DefaultCollectionName { get; init; } = null;

    /// <summary>
    /// Gets or sets a value indicating whether the collection name should be prefixed to the
    /// key names before reading or writing to the Redis store. Default is false.
    /// </summary>
    /// <remarks>
    /// For a record to be indexed by a specific Redis index, the key name must be prefixed with the matching prefix configured on the Redis index.
    /// You can either pass in keys that are already prefixed, or set this option to true to have the collection name prefixed to the key names automatically.
    /// </remarks>
    public bool PrefixCollectionNameToKeyNames { get; init; } = false;

    /// <summary>
    /// Gets or sets the choice of mapper to use when converting between the data model and the Redis record.
    /// </summary>
    public RedisRecordMapperType MapperType { get; init; } = RedisRecordMapperType.Default;

    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the Redis record.
    /// </summary>
    /// <remarks>
    /// Set <see cref="MapperType"/> to <see cref="RedisRecordMapperType.JsonNodeCustomMapper"/> to use this mapper."/>
    /// </remarks>
    public IVectorStoreRecordMapper<TRecord, (string Key, JsonNode Node)>? JsonNodeCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Redis record.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; init; } = null;
}
