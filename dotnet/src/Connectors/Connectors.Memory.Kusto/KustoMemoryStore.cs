// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Kusto.Cloud.Platform.Utils;
using Kusto.Data;
using Kusto.Data.Common;
using Kusto.Data.Net.Client;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Newtonsoft.Json;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

internal static class KustoSerializer
{
    public static string SerializeEmbedding(Embedding<float> embedding)
    {
        return JsonConvert.SerializeObject(embedding.Vector);
    }
    public static Embedding<float> DeserializeEmbedding(string? embedding)
    {
        if (string.IsNullOrEmpty(embedding))
        {
            return default;
        }

        float[]? floatArray = JsonConvert.DeserializeObject<float[]>(embedding!);

        if (floatArray == null)
        {
            return default;
        }

        return new Embedding<float>(floatArray);
    }
    public static string SerializeMetadata(MemoryRecordMetadata metadata)
    {
        if (metadata == null)
        {
            return string.Empty;
        }

        return JsonConvert.SerializeObject(metadata);
    }
    public static MemoryRecordMetadata DeserializeMetadata(string metadata)
    {
        return JsonConvert.DeserializeObject<MemoryRecordMetadata>(metadata)!;
    }
}

internal static class KustoExtensions
{
    public static async ValueTask<T?> FirstOrDefaultAsync<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        if (source == null)
        {
            throw new ArgumentNullException(nameof(source));
        }

        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            return item;
        }

        return default;
    }
}

sealed internal class KustoMemoryRecord
{
    public string Key { get; set; }
    public MemoryRecordMetadata Metadata { get; set; }
    public Embedding<float> Embedding { get; set; }
    public DateTime? Timestamp { get; set; }

    public KustoMemoryRecord(MemoryRecord record) : this(record.Key, record.Metadata, record.Embedding, record.Timestamp?.UtcDateTime) { }

    public KustoMemoryRecord(string key, MemoryRecordMetadata metadata, Embedding<float> embedding, DateTime? timestamp = null)
    {
        this.Key = key;
        this.Metadata = metadata;
        this.Embedding = embedding;
        this.Timestamp = timestamp;
    }

    public KustoMemoryRecord(string key, string metadata, string? embedding, DateTime? timestamp = null)
    {
        this.Key = key;
        this.Metadata = KustoSerializer.DeserializeMetadata(metadata);
        this.Embedding = KustoSerializer.DeserializeEmbedding(embedding);
        this.Timestamp = timestamp;
    }

    public MemoryRecord ToMemoryRecord()
    {
        return new MemoryRecord(this.Metadata, this.Embedding, this.Key, this.Timestamp);
    }

    public void WriteToCsvStream(CsvWriter streamWriter)
    {
        var jsonifiedMetadata = KustoSerializer.SerializeMetadata(this.Metadata);
        var jsonifiedEmbedding = KustoSerializer.SerializeEmbedding(this.Embedding);
        var isoFormattedDate = this.Timestamp?.ToString("o", CultureInfo.InvariantCulture) ?? string.Empty;

        streamWriter.WriteField(this.Key);
        streamWriter.WriteField(jsonifiedMetadata);
        streamWriter.WriteField(jsonifiedEmbedding);
        streamWriter.WriteField(isoFormattedDate);
        streamWriter.CompleteRecord();
    }
}

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Kusto database.
/// </summary>
/// <remarks>The embedded data is saved to the Kusto database specified in the constructor.
/// Similarity search capability is provided through a cosine similarity function (added on first collection creation). Use Kusto's "Table" to implement "Collection".
/// </remarks>
public class KustoMemoryStore : IMemoryStore
{
    private string _database;
    private static ClientRequestProperties GetClientRequestProperties() => new()
    {
        Application = "SemanticKernel",
    };

    private readonly ICslQueryProvider _queryClient;
    private readonly ICslAdminProvider _adminClient;

    private static readonly ColumnSchema[] s_collectionColumns = new ColumnSchema[]
    {
        new ColumnSchema("Key", typeof(string).FullName),
        new ColumnSchema("Metadata", typeof(object).FullName),
        new ColumnSchema("Embedding", typeof(object).FullName),
        new ColumnSchema("Timestamp", typeof(DateTime).FullName),
    };

    private const string c_collectionPrefix = "sk_memory_";
    private static string GetTableName(string collectionName) => c_collectionPrefix + collectionName;
    private static string GetCollectionName(string tableName) => tableName.Substring(c_collectionPrefix.Length);

    /// <summary>
    /// Initializes a new instance of the <see cref="KustoMemoryStore"/> class.
    /// </summary>
    /// <param name="kcsb">Kusto Connection String Builder.</param>
    /// <param name="database">The database used for the tables.</param>
    public KustoMemoryStore(KustoConnectionStringBuilder kcsb, string database)
    {
        this._database = database;
        this._queryClient = KustoClientFactory.CreateCslQueryProvider(kcsb);
        this._adminClient = KustoClientFactory.CreateCslAdminProvider(kcsb);
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this.InitializeVectorFunctionsAsync().ConfigureAwait(false);

        using var resp = await this._adminClient
            .ExecuteControlCommandAsync(
                this._database,
                CslCommandGenerator.GenerateTableCreateCommand(new TableSchema(GetTableName(collectionName), s_collectionColumns)),
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using var resp = await this._adminClient
            .ExecuteControlCommandAsync(
                this._database,
                CslCommandGenerator.GenerateTableDropCommand(GetTableName(collectionName)),
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var result = await this._adminClient
            .ExecuteControlCommandAsync<TablesShowCommandResult>(
                this._database,
                CslCommandGenerator.GenerateTablesShowCommand() + $" | where TableName == '{GetTableName(collectionName)}'",
                GetClientRequestProperties()
            ).ConfigureAwait(false);

        return result.Count() == 1;
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var result = this.GetBatchAsync(collectionName, new[] { key }, withEmbedding, cancellationToken);
        return await result.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var inClauseValue = string.Join(",", keys.Select(k => $"'{k}'"));
        var query = $"{this.GetBaseQuery(collectionName)} " +
            $"| where Key in ({inClauseValue}) " +
            "| project " +
            // Key
            $"{s_collectionColumns[0].Name}, " +
            // Metadata
            $"{s_collectionColumns[1].Name}=tostring({s_collectionColumns[1].Name}), " +
            // Timestamp
            $"{s_collectionColumns[3].Name}, " +
            // Embedding
            $"{s_collectionColumns[2].Name}=tostring({s_collectionColumns[2].Name})";

        if (!withEmbeddings)
        {
            // easiest way to ignore embeddings
            query += " | extend Embedding = ''";
        }

        using var reader = await this._queryClient
            .ExecuteQueryAsync(
                this._database,
                query,
                GetClientRequestProperties(),
                cancellationToken
            ).ConfigureAwait(false);

        while (reader.Read())
        {
            var key = reader.GetString(0);
            var metadata = reader.GetString(1);
            DateTime? timestamp = reader.IsDBNull(2) ? null : reader.GetDateTime(2);
            var _embedding = withEmbeddings ? reader.GetString(3) : default;

            var kustoRecord = new KustoMemoryRecord(key, metadata, _embedding, timestamp);

            yield return kustoRecord.ToMemoryRecord();
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var result = await this._adminClient
            .ExecuteControlCommandAsync<TablesShowCommandResult>(
                this._database,
                CslCommandGenerator.GenerateTablesShowCommand() + $" | where TableName startswith '{c_collectionPrefix}'",
                GetClientRequestProperties()
            ).ConfigureAwait(false);

        foreach (var item in result)
        {
            yield return GetCollectionName(item.TableName);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var result = this.GetNearestMatchesAsync(collectionName, embedding, 1, minRelevanceScore, withEmbedding, cancellationToken);
        return await result.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var similarityQuery = $"{this.GetBaseQuery(collectionName)} | extend similarity=series_cosine_similarity_fl('{KustoSerializer.SerializeEmbedding(embedding)}', {s_collectionColumns[2].Name}, 1, 1)";

        if (minRelevanceScore != 0)
        {
            similarityQuery += $" | where similarity > {minRelevanceScore}";
        }

        similarityQuery += $" | top {limit} by similarity desc";
        // reorder to make it easier to ignore the embedding (key, metadata, timestamp, similarity, embedding
        // Using tostring to make it easier to parse the result. There are probably better ways we should explore
        similarityQuery += "| project " +
            // Key
            $"{s_collectionColumns[0].Name}, " +
            // Metadata
            $"{s_collectionColumns[1].Name}=tostring({s_collectionColumns[1].Name}), " +
            // Timestamp
            $"{s_collectionColumns[3].Name}, " +
            "similarity, " +
            // Embedding
            $"{s_collectionColumns[2].Name}=tostring({s_collectionColumns[2].Name})";

        if (!withEmbeddings)
        {
            similarityQuery += $" | project-away {s_collectionColumns[2].Name} ";
        }

        using var reader = await this._queryClient
            .ExecuteQueryAsync(
                this._database,
                similarityQuery,
                GetClientRequestProperties(),
                cancellationToken
            ).ConfigureAwait(false);
        while (reader.Read())
        {
            var key = reader.GetString(0);
            var metadata = reader.GetString(1);
            DateTime? timestamp = reader.IsDBNull(2) ? null : reader.GetDateTime(2);
            var similarity = reader.GetDouble(3);
            var _embedding = withEmbeddings ? reader.GetString(4) : default;

            var kustoRecord = new KustoMemoryRecord(key, metadata, _embedding, timestamp);

            yield return (kustoRecord.ToMemoryRecord(), similarity);
        }
    }

    /// <inheritdoc/>
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default) => this.RemoveBatchAsync(collectionName, new[] { key }, cancellationToken);

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        if (keys != null)
        {
            var keysString = string.Join(",", keys.Select(k => $"'{k}'"));
            using var resp = await this._adminClient
                .ExecuteControlCommandAsync(
                    this._database,
                    CslCommandGenerator.GenerateDeleteTableRecordsCommand(GetTableName(collectionName), $"{GetTableName(collectionName)} | where Key in ({keysString})"),
                    GetClientRequestProperties()
                ).ConfigureAwait(false);
        }
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        var result = this.UpsertBatchAsync(collectionName, new[] { record }, cancellationToken);
        return await result.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false) ?? string.Empty;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // In Kusto, upserts don't exist because it operates as an append-only store.
        // Nevertheless, given that we have a straightforward primary key (PK), we can simply insert a new record.
        // Our query always selects the latest row of that PK.
        // An interesting scenario arises when performing deletion after many "upserts". 
        // This could turn out to be a heavy operation since, in theory, we might need to remove many outdated versions.
        // Additionally, deleting these records equates to a "soft delete" operation.
        // For simplicity, and under the assumption that upserts are relatively rare in most systems, 
        // we will overlook the potential accumulation of "garbage" records.
        // Kusto is generally efficient with handling large volumes of data.
        using var stream = new MemoryStream();
        using var streamWriter = new StreamWriter(stream);
        var csvWriter = new FastCsvWriter(streamWriter);

        var keys = new List<string>();
        var recordsAsList = records.ToList();
        for (var i = 0; i < recordsAsList.Count; i++)
        {
            var record = recordsAsList[i];
            record.Key = record.Metadata.Id;
            keys.Add(record.Key);
            new KustoMemoryRecord(record).WriteToCsvStream(csvWriter);
        }
        csvWriter.Flush();
        stream.Seek(0, SeekOrigin.Begin);

        var command = CslCommandGenerator.GenerateTableIngestPushCommand(GetTableName(collectionName), false, stream);
        await this._adminClient
            .ExecuteControlCommandAsync(
                this._database,
                command,
                GetClientRequestProperties()
            ).ConfigureAwait(false);

        foreach (var key in keys)
        {
            yield return key;
        }
    }

    private string GetBaseQuery(string collection)
    {
        // Kusto is an append-only store. Although deletions are possible, they are highly discourged,
        // and should only be used in rare cases (see: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/concepts/data-soft-delete#use-cases).
        // As such, the recommended approach for dealing with row updates is versioning.
        // An easy way to achieve this is by using the ingestion time of the record (insertion time).
        return $"{GetTableName(collection)} | summarize arg_max(ingestion_time(), *) by {s_collectionColumns[0].Name} ";
    }

    private async Task InitializeVectorFunctionsAsync()
    {
        var resp = await this._adminClient
            .ExecuteControlCommandAsync<FunctionShowCommandResult>(
                this._database,
                ".create-or-alter function with (docstring = 'Calculate the Cosine similarity of 2 numerical arrays',folder = 'Vector') series_cosine_similarity_fl(vec1:dynamic,vec2:dynamic,vec1_size:real=real(null),vec2_size:real=real(null)) {" +
                "  let dp = series_dot_product(vec1, vec2);" +
                "  let v1l = iff(isnull(vec1_size), sqrt(series_dot_product(vec1, vec1)), vec1_size);" +
                "  let v2l = iff(isnull(vec2_size), sqrt(series_dot_product(vec2, vec2)), vec2_size);" +
                "  dp/(v1l*v2l)" +
                "}",
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }
}
