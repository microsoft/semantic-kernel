// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Options when creating a <see cref="AzureAISearchMemoryRecordService{TDataModel}"/>.
/// </summary>
public sealed class AzureAISearchMemoryRecordServiceOptions<TDataModel>
    where TDataModel : class
{
    /// <summary>
    /// Gets or sets the default collection name to use.
    /// If not provided here, the collection name will need to be provided for each operation or the operation will throw.
    /// </summary>
    public string? DefaultCollectionName { get; init; } = null;

    /// <summary>
    /// Gets or sets the choice of mapper to use when converting between the data model and the azure ai search record.
    /// </summary>
    public AzureAISearchMemoryRecordMapperType MapperType { get; init; } = AzureAISearchMemoryRecordMapperType.Default;

    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the azure ai search record.
    /// </summary>
    /// <remarks>
    /// Set <see cref="MapperType"/> to <see cref="AzureAISearchMemoryRecordMapperType.JsonObjectCustomMapper"/> to use this mapper."/>
    /// </remarks>
    public IMemoryRecordMapper<TDataModel, JsonObject>? JsonObjectCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional memory record definition that defines the schema of the memory record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the data model using reflection.
    /// In this case, the data model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="MemoryRecordKeyAttribute"/>, <see cref="MemoryRecordDataAttribute"/> and <see cref="MemoryRecordVectorAttribute"/>.
    /// </remarks>
    public MemoryRecordDefinition? MemoryRecordDefinition { get; init; } = null;
}
