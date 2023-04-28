// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

internal enum OperationType
{
    Upsert,
    Update,
    Skip
}

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Pinecone Vector database.
/// </summary>
/// <remarks>
/// The Embedding data is saved to a Pinecone Vector database instance that the client is connected to.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// It should be noted that "Collection" in Pinecone's terminology is much different than what Collection means in IMemoryStore.
/// For that reason, we use the term "Index" in Pinecone to refer to what is a "Collection" in IMemoryStore. So, in the case of Pinecone,
///  "Collection" is synonymous with "Index" when referring to IMemoryStore.
/// </remarks>
public class PineconeMemoryStore : IPineconeMemoryStore
{

    /// <summary>
    /// Constructor for a memory store backed by a <see cref="IPineconeClient"/>
    /// </summary>
    public PineconeMemoryStore(
        IPineconeClient pineconeClient,
        ILogger? logger = null)
    {
        this._pineconeClient = pineconeClient;
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <summary>
    ///   Initializes a new instance of the <see cref="PineconeMemoryStore"/> class and ensures that the index exists and is ready.
    /// </summary>
    /// <param name="pineconeEnvironment"> the location of the pinecone server </param>
    /// <param name="apiKey"> the api key for the pinecone server </param>
    /// <param name="indexDefinition"> the index definition </param>
    /// <param name="logger"></param>
    /// <param name="cancellationToken"></param>
    /// <returns> a new instance of the <see cref="PineconeMemoryStore"/> class </returns>
    /// <remarks>
    ///  This is the preferred method of creating a new instance of the <see cref="PineconeMemoryStore"/>
    ///  class because it ensures that the index exists and is ready. I think it makes sense to have this
    ///  method be static because it is a factory method that returns a new instance of the class.
    ///  If the index does not exist, it will be created. If the index exists, it will be connected to.
    ///  If it is a new index, the method will block until it is ready.
    ///  If the index exists but is not ready, it will be connected to and the method will block until it is ready.
    /// </remarks>
    public static async Task<PineconeMemoryStore?> InitializeAsync(
        PineconeEnvironment pineconeEnvironment,
        string apiKey,
        IndexDefinition indexDefinition,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {

        logger ??= NullLogger.Instance;
        PineconeClient client = new(pineconeEnvironment, apiKey, logger);

        bool exists = await client.DoesIndexExistAsync(indexDefinition.Name, cancellationToken).ConfigureAwait(false);

        if (exists)
        {
            if (await client.ConnectToHostAsync(indexDefinition.Name, cancellationToken).ConfigureAwait(true))
            {
                return new PineconeMemoryStore(client, logger);
            }

            logger.LogError("Failed to connect to host.");
            return null;
        }

        string? indexName = await client.CreateIndexAsync(indexDefinition, cancellationToken).ConfigureAwait(false);

        if (!string.IsNullOrEmpty(indexName) && client.Ready)
        {
            return new PineconeMemoryStore(client, logger);
        }

        logger.LogError("Failed to create index.");
        return null;

    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="cancel"></param> 
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (!await this.DoesCollectionExistAsync(collectionName, cancel).ConfigureAwait(false))
        {
            IndexDefinition indexDefinition = IndexDefinition.Create(collectionName);
            await this._pineconeClient.CreateIndexAsync(indexDefinition, cancel).ConfigureAwait(false);
        }
    }

    /// <inheritdoc />
    /// <returns> a list of index names </returns>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._pineconeClient.ListIndexesAsync(cancel).Select(index => index ?? "");
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="cancel"></param>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        return await this._pineconeClient.DoesIndexExistAsync(collectionName, cancel).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="cancel"></param>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (!await this.DoesCollectionExistAsync(collectionName, cancel).ConfigureAwait(false))
        {
            await this._pineconeClient.DeleteIndexAsync(collectionName, cancel).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="record"></param>
    /// <param name="cancel"></param>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return string.Empty;
        }

        Console.WriteLine($"Upserting {record.Metadata.Id} with text {record.Metadata.Text} to {collectionName}");
        (PineconeDocument vectorData, OperationType operationType) = await this.EvaluateAndUpdateMemoryRecordAsync(collectionName, record, "", cancel).ConfigureAwait(false);

        Task request = operationType switch
        {
            OperationType.Upsert => this._pineconeClient.UpsertAsync(collectionName, new[] { vectorData }, "", cancel),
            OperationType.Update => this._pineconeClient.UpdateAsync(collectionName, vectorData, "", cancel),
            OperationType.Skip => Task.CompletedTask,
            _ => Task.CompletedTask
        };

        try
        {
            await request.ConfigureAwait(false);

        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToUpsertVectors,
                $"Failed to upsert due to HttpRequestException: {ex.Message}",
                ex);
        }

        return vectorData.Id;
    }

    /// <inheritdoc />
    public async Task<string> UpsertToNamespaceAsync(string indexName, string indexNamespace, MemoryRecord record, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return string.Empty;
        }

        (PineconeDocument vectorData, OperationType operationType) = await this.EvaluateAndUpdateMemoryRecordAsync(indexName, record, "", cancel).ConfigureAwait(false);

        Task request = operationType switch
        {
            OperationType.Upsert => this._pineconeClient.UpsertAsync(indexName, new[] { vectorData }, indexNamespace, cancel),
            OperationType.Update => this._pineconeClient.UpdateAsync(indexName, vectorData, indexNamespace, cancel),
            OperationType.Skip => Task.CompletedTask,
            _ => Task.CompletedTask
        };

        try
        {
            await request.ConfigureAwait(false);

        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToUpsertVectors,
                $"Failed to upsert due to HttpRequestException: {ex.Message}",
                ex);
        }

        return vectorData.Id;
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="records"></param>
    /// <param name="cancel"></param>
    public async IAsyncEnumerable<string> UpsertBatchAsync(
        string collectionName,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        List<PineconeDocument> upsertDocuments = new();
        List<PineconeDocument> updateDocuments = new();

        foreach (MemoryRecord? record in records)
        {
            (PineconeDocument document, OperationType operationType) = await this.EvaluateAndUpdateMemoryRecordAsync(
                collectionName,
                record,
                "",
                cancel).ConfigureAwait(false);

            // ReSharper disable once SwitchStatementHandlesSomeKnownEnumValuesWithDefault
            switch (operationType)
            {
                case OperationType.Upsert:
                    upsertDocuments.Add(document);
                    break;

                case OperationType.Update:
                    updateDocuments.Add(document);
                    break;

                case OperationType.Skip:
                    yield return document.Id;
                    break;

            }
        }

        List<Task> tasks = new();

        if (upsertDocuments.Count > 0)
        {
            tasks.Add(this._pineconeClient.UpsertAsync(collectionName, upsertDocuments, "", cancel));
        }

        if (updateDocuments.Count > 0)
        {
            IEnumerable<Task> updates = updateDocuments.Select(async d
                => await this._pineconeClient.UpdateAsync(collectionName, d, "", cancel).ConfigureAwait(false));

            tasks.AddRange(updates);
        }

        Console.WriteLine($"UpsertBatchAsync: {upsertDocuments.Count} upserts, {updateDocuments.Count} updates");

        PineconeDocument[] vectorData = upsertDocuments.Concat(updateDocuments).ToArray();

        try
        {
            await Task.WhenAll(tasks).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToUpsertVectors,
                $"Failed to upsert due to HttpRequestException: {ex.Message}",
                ex);
        }

        foreach (PineconeDocument? v in vectorData)
        {
            yield return v.Id;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> UpsertBatchToNamespaceAsync(
        string indexName,
        string indexNamespace,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        List<PineconeDocument> upsertDocuments = new();
        List<PineconeDocument> updateDocuments = new();

        foreach (MemoryRecord? record in records)
        {
            (PineconeDocument document, OperationType operationType) = await this.EvaluateAndUpdateMemoryRecordAsync(
                indexName,
                record,
                indexNamespace,
                cancel).ConfigureAwait(false);

            // ReSharper disable once SwitchStatementHandlesSomeKnownEnumValuesWithDefault
            switch (operationType)
            {
                case OperationType.Upsert:
                    upsertDocuments.Add(document);
                    break;

                case OperationType.Update:

                    updateDocuments.Add(document);
                    break;

                case OperationType.Skip:
                    yield return document.Id;
                    break;

            }
        }

        List<Task> tasks = new();

        if (upsertDocuments.Count > 0)
        {
            tasks.Add(this._pineconeClient.UpsertAsync(indexName, upsertDocuments, indexNamespace, cancel));
        }

        if (updateDocuments.Count > 0)
        {
            IEnumerable<Task> updates = updateDocuments.Select(async d
                => await this._pineconeClient.UpdateAsync(indexName, d, indexNamespace, cancel).ConfigureAwait(false));

            tasks.AddRange(updates);
        }

        Console.WriteLine($"UpsertBatchAsync: {upsertDocuments.Count} upserts, {updateDocuments.Count} updates");

        PineconeDocument[] vectorData = upsertDocuments.Concat(updateDocuments).ToArray();

        try
        {
            await Task.WhenAll(tasks).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToUpsertVectors,
                $"Failed to upsert due to HttpRequestException: {ex.Message}",
                ex);
        }

        foreach (PineconeDocument? v in vectorData)
        {
            yield return v.Id;
        }
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="key"></param>
    /// <param name="withEmbedding"></param>
    /// <param name="cancel"></param>
    public async Task<MemoryRecord?> GetAsync(
        string collectionName,
        string key,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return null;
        }

        try
        {
            await foreach (PineconeDocument? record in this._pineconeClient.FetchVectorsAsync(collectionName,
                new[] { key },
                "",
                withEmbedding, cancel))
            {
                return record?.ToMemoryRecord();
            }
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToGetVectorData,
                $"Failed to get vector data from Pinecone: {ex.Message}",
                ex);
        }
        catch (MemoryException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToConvertPineconeDocumentToMemoryRecord,
                $"Failed deserialize Pinecone response to Memory Record: {ex.Message}",
                ex);
        }

        return null;
    }

    /// <inheritdoc />
    public async Task<MemoryRecord?> GetFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        string key,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return null;
        }

        try
        {
            await foreach (PineconeDocument? record in this._pineconeClient.FetchVectorsAsync(indexName,
                new[] { key },
                indexNamespace,
                withEmbedding, cancel))
            {
                return record?.ToMemoryRecord();
            }
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToGetVectorData,
                $"Failed to get vector data from Pinecone: {ex.Message}",
                ex);
        }
        catch (MemoryException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToConvertPineconeDocumentToMemoryRecord,
                $"Failed deserialize Pinecone response to Memory Record: {ex.Message}",
                ex);
        }

        return null;
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="keys"></param>
    /// <param name="withEmbeddings"></param>
    /// <param name="cancel"></param>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(
        string collectionName,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        foreach (string? key in keys)
        {
            MemoryRecord? record = await this.GetAsync(collectionName, key, withEmbeddings, cancel).ConfigureAwait(false);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<MemoryRecord> GetBatchFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        IEnumerable<string> keys,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        foreach (string? key in keys)
        {
            MemoryRecord? record = await this.GetFromNamespaceAsync(indexName, indexNamespace, key, withEmbeddings, cancel).ConfigureAwait(false);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <summary>
    /// Get a MemoryRecord from the Pinecone Vector database by pointId.
    /// </summary>
    /// <param name="indexName">The name associated with the index to get the Pinecone vector record from.</param>
    /// <param name="documentId">The unique indexed ID associated with the Pinecone vector record to get.</param>
    /// <param name="limit"></param>
    /// <param name="namespace"> The namespace associated with the Pinecone vector record to get.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="PineconeMemoryException"></exception>
    public async IAsyncEnumerable<MemoryRecord?> GetWithDocumentIdAsync(string indexName,
        string documentId,
        int limit = 3,
        string indexNamespace = "",
        bool withEmbedding = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield return null;
        }

        IEnumerable<PineconeDocument?> vectorDataList;

        try
        {
            vectorDataList = await this._pineconeClient
                .QueryAsync(indexName,
                    limit,
                    indexNamespace,
                    null,
                    withEmbedding,
                    true,
                    new Dictionary<string, object>()
                    {
                        { "document_Id", documentId }
                    },
                    cancellationToken: cancel).Take(limit).ToListAsync(cancellationToken: cancel).ConfigureAwait(false);
        }

        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Error getting batch with filter from Pinecone.");
            yield break;
        }

        foreach (PineconeDocument? record in vectorDataList)
        {
            yield return record?.ToMemoryRecord();
        }

    }

    /// <summary>
    /// Get a MemoryRecord from the Pinecone Vector database by a group of pointIds.
    /// </summary>
    /// <param name="indexName">The name associated with the index to get the Pinecone vector records from.</param>
    /// <param name="documentIds">The unique indexed IDs associated with Pinecone vector records to get.</param>
    /// <param name="limit"></param>
    /// <param name="namespace"> The namespace associated with the Pinecone vector records to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<MemoryRecord?> GetWithDocumentIdBatchAsync(string indexName,
        IEnumerable<string> documentIds,
        int limit = 3,
        string indexNamespace = "",
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        foreach (IAsyncEnumerable<MemoryRecord?>? records in documentIds.Select(documentId =>
            this.GetWithDocumentIdAsync(indexName, documentId, limit, indexNamespace, withEmbeddings, cancel)))
        {
            await foreach (MemoryRecord? record in records.WithCancellation(cancel))
            {
                yield return record;
            }
        }
    }

    public async IAsyncEnumerable<MemoryRecord?> GetBatchWithFilterAsync(string indexName,
        Dictionary<string, object> filter,
        int limit = 10,
        string indexNamespace = "",
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        IEnumerable<PineconeDocument?> vectorDataList;

        try
        {
            vectorDataList = await this._pineconeClient
                .QueryAsync(indexName,
                    limit,
                    indexNamespace,
                    null,
                    withEmbeddings,
                    true,
                    filter,
                    cancellationToken: cancel).Take(limit).ToListAsync(cancellationToken: cancel).ConfigureAwait(false);
        }

        catch (HttpRequestException e)
        {
            this._logger.LogError(e, "Error getting batch with filter from Pinecone.");
            yield break;
        }

        foreach (PineconeDocument? record in vectorDataList)
        {
            yield return record?.ToMemoryRecord();
        }
    }

    /// <inheritdoc />
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="key"></param>
    /// <param name="cancel"></param>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            await this._pineconeClient.DeleteAsync(collectionName, new[]
                {
                    key
                },
                cancellationToken: cancel).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Failed to remove vector data from Pinecone {ex.Message}",
                ex);
        }
    }

    /// <inheritdoc />
    public async Task RemoveFromNamespaceAsync(string indexName, string indexNamespace, string key, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            await this._pineconeClient.DeleteAsync(indexName, new[]
                {
                    key
                },
                indexNamespace,
                cancellationToken: cancel).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Failed to remove vector data from Pinecone {ex.Message}",
                ex);
        }
    }

    /// <inheritdoc />
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="keys"></param>
    /// <param name="cancel"></param>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        await Task.WhenAll(keys.Select(async k => await this.RemoveAsync(collectionName, k, cancel).ConfigureAwait(false))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task RemoveBatchFromNamespaceAsync(string indexName, string indexNamespace, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }
        await Task.WhenAll(keys.Select(async k => await this.RemoveFromNamespaceAsync(indexName, indexNamespace, k, cancel).ConfigureAwait(false))).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async Task RemoveWithFilterAsync(
        string indexName,
        Dictionary<string, object> filter,
        string indexNamespace = "",
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            await this._pineconeClient.DeleteAsync(
                indexName,
                default,
                indexNamespace,
                filter,
                cancellationToken: cancel).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Failed to remove vector data from Pinecone {ex.Message}",
                ex);
        }

    }

    /// <summary>
    /// Remove a MemoryRecord from the Pinecone Vector database by pointId.
    /// </summary>
    /// <param name="indexName"> The name associated with the index to remove the Pinecone vector record from.</param>
    /// <param name="namespace">The name associated with a collection of embeddings.</param>
    /// <param name="documentId">The unique indexed ID associated with the Pinecone vector record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="PineconeMemoryException"></exception>
    public async Task RemoveWithDocumentIdAsync(string indexName, string documentId, string indexNamespace, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            await this._pineconeClient.DeleteAsync(indexName, null, indexNamespace, new Dictionary<string, object>()
            {
                { "document_Id", documentId }
            }, cancellationToken: cancel).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Failed to remove vector data from Pinecone {ex.Message}",
                ex);
        }
    }

    /// <summary>
    /// Remove a MemoryRecord from the Pinecone Vector database by a group of pointIds.
    /// </summary>
    /// <param name="indexName"> The name associated with the index to remove the Pinecone vector record from.</param>
    /// <param name="namespace">The name associated with a collection of embeddings.</param>
    /// <param name="documentIds">The unique indexed IDs associated with the Pinecone vector records to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="PineconeMemoryException"></exception>
    public async Task RemoveWithDocumentIdBatchAsync(
        string indexName,
        IEnumerable<string> documentIds,
        string indexNamespace,
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            IEnumerable<Task> tasks = documentIds.Select(async id
                => await this.RemoveWithDocumentIdAsync(indexName, id, indexNamespace, cancel)
                    .ConfigureAwait(false));

            await Task.WhenAll(tasks).ConfigureAwait(false);
        }
        catch (HttpRequestException ex)
        {
            throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToRemoveVectorData,
                $"Error in batch removing data from Pinecone {ex.Message}",
                ex);
        }
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="embedding"> The embedding to search for </param>
    /// <param name="limit"> The maximum number of results to return </param>
    /// <param name="minRelevanceScore"> The minimum relevance score to return </param>
    /// <param name="withEmbeddings"> Whether to return the embeddings with the results </param>
    /// <param name="cancel"></param>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        IAsyncEnumerable<(PineconeDocument, double)> results = this._pineconeClient.GetMostRelevantAsync(
            collectionName,
            embedding.Vector,
            minRelevanceScore,
            limit,
            withEmbeddings,
            true,
            "",
            default,
            cancel);

        await foreach ((PineconeDocument, double) result in results.WithCancellation(cancel))
        {
            yield return (result.Item1.ToMemoryRecord(), result.Item2);
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        IAsyncEnumerable<(PineconeDocument, double)> results = this._pineconeClient.GetMostRelevantAsync(
            indexName,
            embedding.Vector,
            minRelevanceScore,
            limit,
            withEmbeddings,
            true,
            indexNamespace,
            default,
            cancel);

        await foreach ((PineconeDocument, double) result in results.WithCancellation(cancel))
        {
            yield return (result.Item1.ToMemoryRecord(), result.Item2);
        }
    }

    /// <inheritdoc/>
    /// <param name="collectionName"> in the case of Pinecone, collectionName is synonymous with indexName </param>
    /// <param name="embedding"> The embedding to search for </param>
    /// <param name="minRelevanceScore"> The minimum relevance score to return </param>
    /// <param name="withEmbedding"> Whether to return the embeddings with the results </param>
    /// <param name="cancel"></param>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(
        string collectionName,
        Embedding<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return null;
        }

        IAsyncEnumerable<(MemoryRecord, double)> results = this.GetNearestMatchesAsync(
            collectionName,
            embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancel: cancel);

        (MemoryRecord, double) record = await results.FirstOrDefaultAsync(cancel).ConfigureAwait(false);

        return (record.Item1, record.Item2);
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchFromNamespaceAsync(
        string indexName,
        string indexNamespace,
        Embedding<float> embedding,
        double minRelevanceScore = 0,
        bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return null;
        }

        IAsyncEnumerable<(MemoryRecord, double)> results = this.GetNearestMatchesFromNamespaceAsync(
            indexName,
            indexNamespace,
            embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancel: cancel);

        (MemoryRecord, double) record = await results.FirstOrDefaultAsync(cancel).ConfigureAwait(false);

        return (record.Item1, record.Item2);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesWithFilterAsync(
        string indexName,
        Embedding<float> embedding,
        int limit,
        Dictionary<string, object> filter,
        double minRelevanceScore = 0D,
        string indexNamespace = "",
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        IAsyncEnumerable<(PineconeDocument, double)> results = this._pineconeClient.GetMostRelevantAsync(
            indexName,
            embedding.Vector,
            minRelevanceScore,
            limit,
            withEmbeddings,
            true,
            indexNamespace,
            filter,
            cancel);

        await foreach ((PineconeDocument, double) result in results.WithCancellation(cancel))
        {
            yield return (result.Item1.ToMemoryRecord(), result.Item2);
        }
    }

    /// <inheritdoc />
    public async Task ClearNamespaceAsync(string indexName, string indexNamespace, CancellationToken cancellationToken = default)
    {
        await this._pineconeClient.DeleteAsync(indexName, default, indexNamespace, null, true, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string?> ListNamespacesAsync(string indexName, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IndexStats? indexStats = await this._pineconeClient.DescribeIndexStatsAsync(indexName, default, cancellationToken).ConfigureAwait(false);

        if (indexStats is null)
        {
            yield break;
        }

        foreach (string? indexNamespace in indexStats.Namespaces.Keys)
        {
            yield return indexNamespace;
        }
    }

    #region private ================================================================================

    private readonly IPineconeClient _pineconeClient;
    private readonly ILogger _logger;

    private async Task<(PineconeDocument, OperationType)> EvaluateAndUpdateMemoryRecordAsync(
        string indexName,
        MemoryRecord record,
        string indexNamespace = "",
        CancellationToken cancel = default)
    {
        string key = !string.IsNullOrEmpty(record.Key)
            ? record.Key
            : record.Metadata.Id;

        PineconeDocument vectorData = record.ToPineconeDocument();

        PineconeDocument? existingRecord = await this._pineconeClient.FetchVectorsAsync(indexName, new[] { key }, indexNamespace, false, cancel)
            .FirstOrDefaultAsync(cancel).ConfigureAwait(false);

        if (existingRecord is null)
        {
            Console.WriteLine("No existing record found with ID: " + key);
            return (vectorData, OperationType.Upsert);
        }

        // compare metadata dictionaries
        if (existingRecord.Metadata != null && vectorData.Metadata != null)
        {
            if (existingRecord.Metadata.SequenceEqual(vectorData.Metadata))
            {
                Console.WriteLine("Existing record found with matching metadata, skipping: " + key);
                return (vectorData, OperationType.Skip);
            }
        }
        Console.WriteLine("Existing record found with ID: " + key + ", updating");
        return (vectorData, OperationType.Update);
    }

    #endregion

}
