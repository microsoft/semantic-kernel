// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Empty qdrant response for requests that return nothing but status / error.
/// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes. Justification: deserialized by QdrantVectorDbClient.DeleteVectorsByIdAsync & QdrantVectorDbClient.DeleteVectorByPayloadIdAsync
internal sealed class DeleteVectorsResponse : QdrantResponse
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
{
}
