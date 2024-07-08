// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using OpenAI;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Supports management operations for a <see cref="VectorStore"/>>.
/// </summary>
public sealed class OpenAIVectorStore
{
    private readonly VectorStoreClient _client;

    /// <summary>
    /// The identifier of the targeted vector store
    /// </summary>
    public string VectorStoreId { get; }

    /// <summary>
    /// List all vector stores.
    /// </summary>
    /// <param name="config">Configuration for accessing the vector-store service.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An enumeration of <see cref="VectorStore"/> models.</returns>
    public static IAsyncEnumerable<VectorStore> GetVectorStoresAsync(OpenAIServiceConfiguration config, CancellationToken cancellationToken = default)
    {
        OpenAIClient openAIClient = OpenAIClientFactory.CreateClient(config);
        VectorStoreClient client = openAIClient.GetVectorStoreClient();

        return client.GetVectorStoresAsync(ListOrder.NewestFirst, cancellationToken);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIVectorStore"/> class.
    /// </summary>
    /// <param name="vectorStoreId">The identifier of the targeted vector store</param>
    /// <param name="config">Configuration for accessing the vector-store service.</param>
    public OpenAIVectorStore(string vectorStoreId, OpenAIServiceConfiguration config)
    {
        OpenAIClient openAIClient = OpenAIClientFactory.CreateClient(config);
        this._client = openAIClient.GetVectorStoreClient();

        this.VectorStoreId = vectorStoreId;
    }

    /// <summary>
    /// Add a file from the vector store.
    /// </summary>
    /// <param name="fileId">The file to add, by identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task AddFileAsync(string fileId, CancellationToken cancellationToken = default) =>
        await this._client.AddFileToVectorStoreAsync(this.VectorStoreId, fileId, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// Deletes the entire vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<bool> DeleteAsync(CancellationToken cancellationToken = default) =>
        await this._client.DeleteVectorStoreAsync(this.VectorStoreId, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// List the files (by identifier) in the vector store.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<string> GetFilesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (VectorStoreFileAssociation file in this._client.GetFileAssociationsAsync(this.VectorStoreId, ListOrder.NewestFirst, filter: null, cancellationToken).ConfigureAwait(false))
        {
            yield return file.FileId;
        }
    }

    /// <summary>
    /// Remove a file from the vector store.
    /// </summary>
    /// <param name="fileId">The file to remove, by identifier.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public async Task<bool> RemoveFileAsync(string fileId, CancellationToken cancellationToken = default) =>
        await this._client.RemoveFileFromStoreAsync(this.VectorStoreId, fileId, cancellationToken).ConfigureAwait(false);
}
