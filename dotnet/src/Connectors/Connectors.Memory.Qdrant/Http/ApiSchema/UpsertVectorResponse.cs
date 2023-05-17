// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
internal sealed class UpsertVectorResponse : QdrantResponse
{
    /// <summary>
    /// Upsert result information object
    /// </summary>
    [JsonPropertyName("result")]
    public UpdateResult Result { get; set; }

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="result"></param>
    [JsonConstructor]
    public UpsertVectorResponse(UpdateResult result)
    {
        this.Result = result;
    }

    internal sealed class UpdateResult
    {
        /// <summary>
        /// Sequential Number of the Operation
        /// </summary>
        [JsonPropertyName("operation_id")]
        public int OperationId { get; set; }

        /// <summary>
        /// acknowledged - Request is saved to WAL and will be process in a queue.
        /// completed - Request is completed, changes are actual.
        /// </summary>
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;
    }
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
