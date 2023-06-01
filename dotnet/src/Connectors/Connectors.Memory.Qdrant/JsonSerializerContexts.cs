// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(CreateCollectionRequest))]
[JsonSerializable(typeof(DeleteVectorsRequest))]
[JsonSerializable(typeof(GetVectorsRequest))]
[JsonSerializable(typeof(GetVectorsResponse))]
[JsonSerializable(typeof(JsonElement))]
[JsonSerializable(typeof(ListCollectionsResponse))]
[JsonSerializable(typeof(QdrantResponse))]
[JsonSerializable(typeof(SearchVectorsRequest))]
[JsonSerializable(typeof(SearchVectorsResponse))]
[JsonSerializable(typeof(UpsertVectorResponse))]
[JsonSerializable(typeof(UpsertVectorRequest))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
}
