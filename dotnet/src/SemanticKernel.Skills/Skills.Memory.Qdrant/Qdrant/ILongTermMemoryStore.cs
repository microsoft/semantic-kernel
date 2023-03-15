// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Storage;
using Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant;

internal interface ILongTermMemoryStore<TEmbedding> : IQdrantMemoryStore<TEmbedding>, IMemoryStore<TEmbedding>
    where TEmbedding : unmanaged
{
}
