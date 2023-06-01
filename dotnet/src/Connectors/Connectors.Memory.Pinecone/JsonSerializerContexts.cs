// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(ConfigureIndexRequest))]
[JsonSerializable(typeof(DeleteRequest))]
[JsonSerializable(typeof(DescribeIndexStatsRequest))]
[JsonSerializable(typeof(Dictionary<string, object>))]
[JsonSerializable(typeof(FetchResponse))]
[JsonSerializable(typeof(IndexDefinition))]
[JsonSerializable(typeof(IndexStats))]
[JsonSerializable(typeof(PineconeIndex))]
[JsonSerializable(typeof(QueryRequest))]
[JsonSerializable(typeof(QueryResponse))]
[JsonSerializable(typeof(string[]))]
[JsonSerializable(typeof(UpdateVectorRequest))]
[JsonSerializable(typeof(UpsertRequest))]
[JsonSerializable(typeof(UpsertResponse))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
    public static readonly SourceGenerationContext WithPineconeOptions = new(PineconeUtils.DefaultSerializerOptions);
}
