// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma.Http.ApiSchema;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

public interface IChromaClient
{
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    Task<ChromaCollectionModel?> GetCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);

    IAsyncEnumerable<string> ListCollectionsAsync(CancellationToken cancellationToken = default);

    Task AddEmbeddingsAsync(string collectionId, string[] ids, float[][] embeddings, object[]? metadatas = null, CancellationToken cancellationToken = default);

    Task<ChromaEmbeddingsModel> GetEmbeddingsAsync(string collectionId, string[] ids, string[]? include = null, CancellationToken cancellationToken = default);

    Task DeleteEmbeddingsAsync(string collectionId, string[] ids, CancellationToken cancellationToken = default);

    Task<ChromaQueryResultModel> QueryEmbeddingsAsync(string collectionId, float[][] queryEmbeddings, int nResults, string[]? include = null, CancellationToken cancellationToken = default);
}
