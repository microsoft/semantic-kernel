// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using OpenAI;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// %%%
/// </summary>
public sealed class OpenAIVectorStore
{
    private readonly VectorStoreClient _client;

    /// <summary>
    /// %%%
    /// </summary>
    public string VectorStoreId { get; }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="config"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public static IAsyncEnumerable<VectorStore> GetVectorStoresAsync(OpenAIConfiguration config, CancellationToken cancellationToken = default)
    {
        OpenAIClient openAIClient = OpenAIClientFactory.CreateClient(config);
        VectorStoreClient client = openAIClient.GetVectorStoreClient();

        return client.GetVectorStoresAsync(ListOrder.NewestFirst, cancellationToken);
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="vectorStoreId"></param>
    /// <param name="config"></param>
    public OpenAIVectorStore(string vectorStoreId, OpenAIConfiguration config)
    {
        OpenAIClient openAIClient = OpenAIClientFactory.CreateClient(config);
        this._client = openAIClient.GetVectorStoreClient();

        this.VectorStoreId = vectorStoreId;
    }

    // %%% BATCH JOBS ???

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="fileId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task AddFileAsync(string fileId, CancellationToken cancellationToken = default) =>
        await this._client.AddFileToVectorStoreAsync(this.VectorStoreId, fileId, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<bool> DeleteAsync(CancellationToken cancellationToken = default) =>
        await this._client.DeleteVectorStoreAsync(this.VectorStoreId, cancellationToken).ConfigureAwait(false);

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async IAsyncEnumerable<string> GetFilesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (VectorStoreFileAssociation file in this._client.GetFileAssociationsAsync(this.VectorStoreId, ListOrder.NewestFirst, filter: null, cancellationToken).ConfigureAwait(false)) // %%% FILTER
        {
            yield return file.FileId;
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="fileId"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<bool> RemoveFileAsync(string fileId, CancellationToken cancellationToken = default) =>
        await this._client.RemoveFileFromStoreAsync(this.VectorStoreId, fileId, cancellationToken).ConfigureAwait(false);
}
