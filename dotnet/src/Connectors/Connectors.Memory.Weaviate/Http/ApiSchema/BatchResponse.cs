// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.JsonConverter;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.ApiSchema;

// ReSharper disable once ClassNeverInstantiated.Global
internal sealed class BatchResponse : WeaviateObject
{
    public Deprecation[]? Deprecations { get; set; }
    public ObjectResponseResult? Result { get; set; }

    [JsonConverter(typeof(UnixSecondsDateTimeJsonConverter))]
    [JsonPropertyName("creationTimeUnix")]
    public DateTime? CreationTime { get; set; }

    [JsonConverter(typeof(UnixSecondsDateTimeJsonConverter))]
    [JsonPropertyName("lastUpdateTimeUnix")]
    public DateTime? LastUpdateTime { get; set; }
}
