// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

internal sealed class DeleteVectorsResponse : QdrantResponse
{
    [JsonPropertyName("result")]
    public DeleteVectorsResult? Result { get; set; }

    internal class DeleteVectorsResult
    {
        [JsonPropertyName("operation_id")]
        public int OperationId { get; set; }

        [JsonPropertyName("status")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Status { get; set; }
    }
}
