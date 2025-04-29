// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

// ReSharper disable once ClassNeverInstantiated.Global
#pragma warning disable CA1812 // 'BatchResponse' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class BatchResponse : WeaviateObject
#pragma warning restore CA1812 // 'BatchResponse' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
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
