#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Abstract;

internal interface IEmbeddingsClient
{
    /// <summary>
    /// Generates embeddings for the given data asynchronously.
    /// </summary>
    /// <param name="data">The list of strings to generate embeddings for.</param>
    /// <param name="cancellationToken">The cancellation token to cancel the operation.</param>
    /// <returns>Result contains a list of read-only memories of floats representing the generated embeddings.</returns>
    Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(
        IList<string> data,
        CancellationToken cancellationToken = default);
}
