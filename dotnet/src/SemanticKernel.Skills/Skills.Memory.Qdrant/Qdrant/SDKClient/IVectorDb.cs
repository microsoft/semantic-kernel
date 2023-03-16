// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient;

internal interface IVectorDb
{
    public Task<IVectorDbCollection> GetCollectionAsync(string collectionName);
    public Task CreateCollectionIfMissing(string collectionName, int vectorSize);
    public Task DeleteCollection(string collectionName);
}
