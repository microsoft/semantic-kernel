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
}
