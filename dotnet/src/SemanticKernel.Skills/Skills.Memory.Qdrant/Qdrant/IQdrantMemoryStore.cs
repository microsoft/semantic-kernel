// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;

namespace Microsoft.SemanticKernel.Skills.Memory.VectorDB;

internal interface IQdrantMemoryStore<TEmbedding> : IDataStore<VectorRecordData<TEmbedding>>
    where TEmbedding : unmanaged
{
}
