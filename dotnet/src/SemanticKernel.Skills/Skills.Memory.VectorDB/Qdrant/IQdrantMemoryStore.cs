// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory.Storage;
using Qdrant.DotNet;

namespace Microsoft.SemanticKernel.Skills.Memory.VectorDB;

internal interface IQdrantMemoryStore<TEmbedding> : IDataStore<VectorRecordData<TEmbedding>>
    where TEmbedding : unmanaged
{
}
