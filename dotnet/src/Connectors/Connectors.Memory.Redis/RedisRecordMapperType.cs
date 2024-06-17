// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// The types of mapper supported by <see cref="RedisVectorRecordStore{TRecord}"/>.
/// </summary>
public enum RedisRecordMapperType
{
    /// <summary>
    /// Use the default semantic kernel mapper that uses property attributes to determine how to map fields.
    /// </summary>
    Default,

    /// <summary>
    /// Use a custom mapper between <see cref="JsonNode"/> and the data model.
    /// </summary>
    JsonNodeCustomMapper
}
