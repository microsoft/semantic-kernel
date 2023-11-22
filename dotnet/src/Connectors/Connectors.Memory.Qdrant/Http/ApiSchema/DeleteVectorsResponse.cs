// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;

/// <summary>
/// Empty qdrant response for requests that return nothing but status / error.
/// </summary>
internal sealed class DeleteVectorsResponse : QdrantResponse
{
}
