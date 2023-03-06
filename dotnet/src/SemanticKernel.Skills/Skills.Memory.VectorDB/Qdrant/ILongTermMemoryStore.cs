// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory.Storage;
using Qdrant.DotNet;

//namespace Microsoft.SemanticKernel.Connectors.VectorDB.Qdrant;
namespace Microsoft.SemanticKernel.Skills.Memory.VectorDB;
internal interface ILongTermMemoryStore<TEmbedding> : IDataStore<VectorRecordData<TEmbedding>>, IEmbeddingIndex<TEmbedding>
    where TEmbedding: unmanaged
{
}
