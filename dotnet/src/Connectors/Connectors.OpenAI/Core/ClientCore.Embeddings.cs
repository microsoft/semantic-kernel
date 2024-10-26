// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using OpenAI.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="targetModel">Target model to generate embeddings from</param>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    internal async Task<IList<ReadOnlyMemory<float>>> GetEmbeddingsAsync(
        string targetModel,
        IList<string> data,
        Kernel? kernel,
        int? dimensions,
        CancellationToken cancellationToken)
    {
        var result = new List<ReadOnlyMemory<float>>(data.Count);

        if (data.Count > 0)
        {
            var embeddingsOptions = new EmbeddingGenerationOptions()
            {
                Dimensions = dimensions
            };
            ClientResult<EmbeddingCollection> response = await RunRequestAsync(() => this.Client!.GetEmbeddingClient(targetModel).GenerateEmbeddingsAsync(data, embeddingsOptions, cancellationToken)).ConfigureAwait(false);
            ClientResult<EmbeddingCollection> response = await RunRequestAsync(() => this.Client!.GetEmbeddingClient(targetModel).GenerateEmbeddingsAsync(data, embeddingsOptions, cancellationToken)).ConfigureAwait(false);
            ClientResult<OpenAIEmbeddingCollection> response = await RunRequestAsync(() => this.Client!.GetEmbeddingClient(targetModel).GenerateEmbeddingsAsync(data, embeddingsOptions, cancellationToken)).ConfigureAwait(false);
            ClientResult<OpenAIEmbeddingCollection> response = await RunRequestAsync(() => this.Client!.GetEmbeddingClient(targetModel).GenerateEmbeddingsAsync(data, embeddingsOptions, cancellationToken)).ConfigureAwait(false);
            ClientResult<OpenAIEmbeddingCollection> response = await RunRequestAsync(() => this.Client!.GetEmbeddingClient(targetModel).GenerateEmbeddingsAsync(data, embeddingsOptions, cancellationToken)).ConfigureAwait(false);
            var embeddings = response.Value;

            if (embeddings.Count != data.Count)
            {
                throw new KernelException($"Expected {data.Count} text embedding(s), but received {embeddings.Count}");
            }

            for (var i = 0; i < embeddings.Count; i++)
            {
                result.Add(embeddings[i].Vector);
                result.Add(embeddings[i].Vector);
                result.Add(embeddings[i].ToFloats());
                result.Add(embeddings[i].ToFloats());
                result.Add(embeddings[i].ToFloats());
                result.Add(embeddings[i].ToFloats());
            }
        }

        return result;
    }
}
