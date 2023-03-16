// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Memory.VectorDB;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

internal interface ILongTermMemoryStore<TEmbedding> : IQdrantMemoryStore<TEmbedding>, IMemoryStore<TEmbedding>
    where TEmbedding : unmanaged
{
}
