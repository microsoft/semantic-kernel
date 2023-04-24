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

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> for Pinecone Vector database.
/// </summary>
/// <remarks>
/// The Embedding data is saved to a Pinecone Vector database instance that the client is connected to.
/// The embedding data persists between subsequent instances and has similarity search capability.
/// </remarks>
public class PineconeMemoryStore : IPineconeMemoryStore
{

    /// <summary>
    /// Constructor for a memory store backed by a <see cref="IPineconeClient"/>
    /// </summary>
    private PineconeMemoryStore(
        IPineconeClient pineconeClient,
        ILogger? logger = null)
    {
        this._pineconeClient = pineconeClient;
        this._logger ??= NullLogger.Instance;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (!await this.DoesCollectionExistAsync(collectionName, cancel))
        {
            IndexDefinition indexDefinition = IndexDefinition.Create(collectionName);
            await this._pineconeClient.CreateIndexAsync(indexDefinition, cancel);
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._pineconeClient.ListIndexesAsync(cancel).Select(index => index ?? "");
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        return await this._pineconeClient.DoesIndexExistAsync(collectionName, cancel);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        if (!await this.DoesCollectionExistAsync(collectionName, cancel))
        {
            await this._pineconeClient.DeleteIndexAsync(collectionName, cancel);
        }
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return string.Empty;
        }

        PineconeDocument? vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, "", cancel);

        if (vectorData == null)
        {
            throw new PineconeMemoryException(PineconeMemoryException.ErrorCodes.FailedToConvertMemoryRecordToPineconeDocument,
                $"Failed to convert MemoryRecord to PineconeDocument");
        }

        try
        {
            await this._pineconeClient.UpsertAsync(collectionName,
                new[] { vectorData },
                "",
                cancel);
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
    public async Task<string> UpsertToNamespaceAsync(string collectionName, string nameSpace, MemoryRecord record, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return string.Empty;
        }

        PineconeDocument? vectorData = await this.ConvertFromMemoryRecordAsync(collectionName, record, nameSpace, cancel);

        if (vectorData == null)
        {
            throw new PineconeMemoryException(PineconeMemoryException.ErrorCodes.FailedToConvertMemoryRecordToPineconeDocument,
                $"Failed to convert MemoryRecord to PineconeDocument");
        }

        try
        {
            await this._pineconeClient.UpsertAsync(collectionName,
                new[] { vectorData },
                nameSpace,
                cancel);
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

        Task<PineconeDocument[]>? tasks = Task.WhenAll(records.Select(async r
            => await this.ConvertFromMemoryRecordAsync(collectionName, r, "", cancel)));

        PineconeDocument[] vectorData = await tasks;

        try
        {
            await this._pineconeClient.UpsertAsync(collectionName,
                vectorData,
                "",
                cancel);
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
        string collectionName,
        string nameSpace,
        IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        Task<PineconeDocument[]>? tasks = Task.WhenAll(records.Select(async r
            => await this.ConvertFromMemoryRecordAsync(collectionName, r, nameSpace, cancel)));

        PineconeDocument[] vectorData = await tasks;

        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        try
        {
            await this._pineconeClient.UpsertAsync(collectionName,
                vectorData,
                nameSpace,
                cancel);
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
        string collectionName,
        string nameSpace,
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
                nameSpace,
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
            MemoryRecord? record = await this.GetAsync(collectionName, key, withEmbeddings, cancel);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<MemoryRecord> GetBatchFromNamespaceAsync(
        string collectionName,
        string nameSpace,
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
            MemoryRecord? record = await this.GetFromNamespaceAsync(collectionName, nameSpace, key, withEmbeddings, cancel);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <summary>
    /// Get a MemoryRecord from the Pinecone Vector database by pointId.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointId">The unique indexed ID associated with the Pinecone vector record to get.</param>
    /// <param name="nameSpace"> The namespace associated with the Pinecone vector record to get.</param>
    /// <param name="withEmbedding">If true, the embedding will be returned in the memory record.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="PineconeMemoryException"></exception>
    public async Task<MemoryRecord?> GetWithPointIdAsync(
        string collectionName,
        string pointId,
        string nameSpace = "",
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
            IAsyncEnumerable<PineconeDocument?> vectorDataList = this._pineconeClient
                .FetchVectorsAsync(collectionName,
                    new[] { pointId },
                    nameSpace,
                    withEmbedding,
                    cancel);

            PineconeDocument? vectorData = await vectorDataList.FirstOrDefaultAsync(cancel);

            return vectorData?.ToMemoryRecord();
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
    }

    /// <summary>
    /// Get a MemoryRecord from the Pinecone Vector database by a group of pointIds.
    /// </summary>
    /// <param name="collectionName">The name associated with a collection of embeddings.</param>
    /// <param name="pointIds">The unique indexed IDs associated with Pinecone vector records to get.</param>
    /// <param name="nameSpace"> The namespace associated with the Pinecone vector records to get.</param>
    /// <param name="withEmbeddings">If true, the embeddings will be returned in the memory records.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    public async IAsyncEnumerable<MemoryRecord> GetWithPointIdBatchAsync(
        string collectionName,
        IEnumerable<string> pointIds,
        string nameSpace = "",
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            yield break;
        }

        IAsyncEnumerable<PineconeDocument?> vectorDataList = this._pineconeClient
            .FetchVectorsAsync(collectionName,
                pointIds,
                nameSpace,
                withEmbeddings,
                cancel);

        await foreach (PineconeDocument? vectorData in vectorDataList.WithCancellation(cancel))
        {

            yield return (vectorData ?? throw new PineconeMemoryException(
                PineconeMemoryException.ErrorCodes.FailedToGetVectorData,
                $"Failed to get vector data from Pinecone: {vectorData}")).ToMemoryRecord();
        }
    }

    /// <inheritdoc />
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
                cancellationToken: cancel);
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
    public async Task RemoveFromNamespaceAsync(string indexName, string nameSpace, string key, CancellationToken cancel = default)
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
                nameSpace,
                cancellationToken: cancel);
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
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        await Task.WhenAll(keys.Select(async k => await this.RemoveAsync(collectionName, k, cancel)));
    }

    /// <inheritdoc />
    public async Task RemoveBatchFromNamespaceAsync(string collectionName, string nameSpace, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }
        await Task.WhenAll(keys.Select(async k => await this.RemoveFromNamespaceAsync(collectionName, nameSpace, k, cancel)));
    }

    /// <inheritdoc />
    public async Task RemoveWithFilterAsync(
        string collectionName,
        Dictionary<string, object> filter,
        string nameSpace = "",
        CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        await this._pineconeClient.DeleteAsync(
            collectionName,
            default,
            nameSpace,
            filter,
            cancellationToken: cancel).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove a MemoryRecord from the Pinecone Vector database by pointId.
    /// </summary>
    /// <param name="nameSpace">The name associated with a collection of embeddings.</param>
    /// <param name="indexName"></param>
    /// <param name="pointId">The unique indexed ID associated with the Pinecone vector record to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="PineconeMemoryException"></exception>
    public async Task RemoveWithPointIdAsync(string indexName, string pointId, string nameSpace, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            await this._pineconeClient.DeleteAsync(indexName, new[] { pointId }, nameSpace, cancellationToken: cancel);
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
    /// <param name="nameSpace">The name associated with a collection of embeddings.</param>
    /// <param name="indexName"></param>
    /// <param name="pointIds">The unique indexed IDs associated with the Pinecone vector records to remove.</param>
    /// <param name="cancel">Cancellation token.</param>
    /// <returns></returns>
    /// <exception cref="PineconeMemoryException"></exception>
    public async Task RemoveWithPointIdBatchAsync(string indexName, IEnumerable<string> pointIds, string nameSpace, CancellationToken cancel = default)
    {
        if (!this._pineconeClient.Ready)
        {
            this._logger.LogError("Pinecone client is not ready.");
            return;
        }

        try
        {
            await this._pineconeClient.DeleteAsync(indexName, pointIds, nameSpace, cancellationToken: cancel);
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
        string collectionName,
        string nameSpace,
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
            nameSpace,
            default,
            cancel);

        await foreach ((PineconeDocument, double) result in results.WithCancellation(cancel))
        {
            yield return (result.Item1.ToMemoryRecord(), result.Item2);
        }
    }

    /// <inheritdoc/>
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

        (MemoryRecord, double) record = await results.FirstOrDefaultAsync(cancel);

        return (record.Item1, record.Item2);
    }

    /// <inheritdoc />
    public async Task<(MemoryRecord, double)?> GetNearestMatchFromNamespaceAsync(
        string collectionName,
        string nameSpace,
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
            collectionName,
            nameSpace,
            embedding,
            minRelevanceScore: minRelevanceScore,
            limit: 1,
            withEmbeddings: withEmbedding,
            cancel: cancel);

        (MemoryRecord, double) record = await results.FirstOrDefaultAsync(cancel);

        return (record.Item1, record.Item2);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesWithFilterAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        Dictionary<string, object> filter,
        double minRelevanceScore = 0D,
        string nameSpace = "",
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
            nameSpace,
            filter,
            cancel);

        await foreach ((PineconeDocument, double) result in results.WithCancellation(cancel))
        {
            yield return (result.Item1.ToMemoryRecord(), result.Item2);
        }
    }

    /// <inheritdoc />
    public async Task ClearNamespaceAsync(string indexName, string nameSpace, CancellationToken cancellationToken = default)
    {
        await this._pineconeClient.DeleteAsync(indexName, default, nameSpace, null, true, cancellationToken);
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string?> ListNamespacesAsync(string indexName, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IndexStats? indexStats = await this._pineconeClient.DescribeIndexStatsAsync(indexName, default, cancellationToken);

        if (indexStats is null)
        {
            yield break;
        }

        foreach (string? nameSpace in indexStats.Namespaces.Keys)
        {
            yield return nameSpace;
        }
    }

    public static async Task<PineconeMemoryStore?> InitializeAsync(
        PineconeEnvironment pineconeEnvironment,
        string apiKey,
        IndexDefinition indexDefinition,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {

        logger ??= NullLogger.Instance;
        PineconeClient client = new(pineconeEnvironment, apiKey, logger);

        bool exists = await client.DoesIndexExistAsync(indexDefinition.Name, cancellationToken);

        if (exists)
        {
            if (await client.ConnectToHostAsync(indexDefinition.Name, cancellationToken))
            {
                return new PineconeMemoryStore(client, logger);
            }

            logger.LogError("Failed to connect to host.");
            return null;
        }

        string? indexName = await client.CreateIndexAsync(indexDefinition, cancellationToken);

        if (!string.IsNullOrEmpty(indexName) && client.Ready)
        {
            return new PineconeMemoryStore(client, logger);
        }

        logger.LogError("Failed to create index.");
        return null;

    }

    #region private ================================================================================

    private readonly IPineconeClient _pineconeClient;
    private readonly ILogger _logger;

    private async Task<PineconeDocument> ConvertFromMemoryRecordAsync(
        string indexName,
        MemoryRecord record,
        string nameSpace = "",
        CancellationToken cancel = default)
    {
        string pointId;

        // Check if a database key has been provided for update
        if (!string.IsNullOrEmpty(record.Key))
        {
            pointId = record.Key;
        }
        // Check if the data store contains a record with the provided metadata ID
        else
        {
            PineconeDocument? existingRecord = await this._pineconeClient
                .FetchVectorsAsync(indexName, new[] { record.Key }, nameSpace, cancellationToken: cancel)
                .FirstOrDefaultAsync(cancel);

            if (existingRecord != null)
            {
                Console.WriteLine("Found existing record with ID: " + record.Key);
                pointId = existingRecord.Id;
            }
            else
            {
                do // Generate a new ID until a unique one is found (more than one pass should be exceedingly rare)
                {
                    // If no matching record can be found, generate an ID for the new record
                    pointId = Guid.NewGuid().ToString();
                    existingRecord = await this._pineconeClient
                        .FetchVectorsAsync(indexName, new[] { pointId }, nameSpace, cancellationToken: cancel)
                        .FirstOrDefaultAsync(cancel);
                }
                while (existingRecord != null);
            }
        }

        PineconeDocument? vectorData = record.ToPineconeDocument();

        if (vectorData == null)
        {
            throw new PineconeMemoryException(PineconeMemoryException.ErrorCodes.FailedToConvertMemoryRecordToPineconeDocument,
                $"Failed to convert MemoryRecord to PineconeDocument");
        }

        return vectorData;
    }

    #endregion

}
