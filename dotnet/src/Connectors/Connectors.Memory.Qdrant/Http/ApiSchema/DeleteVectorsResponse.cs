// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Empty qdrant response for requests that return nothing but status / error.
/// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes. Justification: deserialized by QdrantVectorDbClient.DeleteVectorsByIdAsync & QdrantVectorDbClient.DeleteVectorByPayloadIdAsync
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and QdrantVectorStore")]
internal sealed class DeleteVectorsResponse : QdrantResponse;
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
