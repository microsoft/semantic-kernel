// Copyright (c) Microsoft. All rights reserved.

using Newtonsoft.Json;

// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

public enum AzureCosmosDBVectorSearchType
{
    [JsonProperty("vector_ivf")]
    VectorIVF,

    [JsonProperty("vector_hnsw")]
    VectorHNSW
}
