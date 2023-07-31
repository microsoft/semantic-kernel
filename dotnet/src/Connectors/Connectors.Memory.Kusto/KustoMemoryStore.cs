// Copyright (c) Microsoft. All rights reserved.

using System.Data;
using System.Globalization;
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
        if (embedding == null)
        {
            return string.Empty;
        }

        return JsonConvert.SerializeObject(embedding.Vector);
    }
    public static Embedding<float> DeserializeEmbedding(string embedding)
    {
        if (string.IsNullOrEmpty(embedding))
        {
            return default;
        }

        float[] floatArray = JsonConvert.DeserializeObject<float[]>(embedding);
        return new Embedding<float>(floatArray);
    }
    public static string SerializeMetadata(MemoryRecordMetadata metadata)
    {
        if (metadata == null)
        {
            return string.Empty;
        }

        return JsonConvert.SerializeObject(metadata).Replace("\"", "\"\"");
    }
    public static MemoryRecordMetadata? DeserializeMetadata(string metadata)
    {
        if (string.IsNullOrEmpty(metadata))
        {
            return default;
        }

        return JsonConvert.DeserializeObject<MemoryRecordMetadata>(metadata);
    }
}

internal static class KustoExtensions
{
    public static async ValueTask<T?> FirstOrDefaultAsync<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            return item;
        }

        return default;
    }
}

internal class KustoMemoryRecord
{
    public string Key { get; set; }
    public MemoryRecordMetadata Metadata { get; set; }
    public Embedding<float> Embedding { get; set; }
    public DateTime? Timestamp { get; set; }

    public KustoMemoryRecord() { }

    public KustoMemoryRecord(MemoryRecord record) : this(record.Key, record.Metadata, record.Embedding, record.Timestamp?.UtcDateTime) { }

    public KustoMemoryRecord(string key, MemoryRecordMetadata metadata, Embedding<float> embedding, DateTime? timestamp = null)
    {
        this.Key = key;
        this.Metadata = metadata;
        this.Embedding = embedding;
        this.Timestamp = timestamp;
    }

    public KustoMemoryRecord(string key, string metadata, string embedding, DateTime? timestamp = null)
    {
        this.Key = key;
        this.Metadata = KustoSerializer.DeserializeMetadata(metadata);
        this.Embedding = KustoSerializer.DeserializeEmbedding(embedding);
        this.Timestamp = timestamp;
    }

    public MemoryRecord ToMemoryRecord()
    {
        return new MemoryRecord((MemoryRecordMetadata)this.Metadata, (Embedding<float>)this.Embedding, this.Key, this.Timestamp);
    }

    public string ToCsvString()
    {
        // Escapse string values in metadata according the Kusto csv escaping rules, whicm means replacing all \" (backslash double qoutes) with "" (two double qoutes)
        var jsonifiedMetadata = KustoSerializer.SerializeMetadata(this.Metadata);
        var jsonifiedEmbedding = KustoSerializer.SerializeEmbedding(this.Embedding);
        var isoFormattedDate = this.Timestamp?.ToString("o", CultureInfo.InvariantCulture) ?? string.Empty;
        return $"\"{this.Key}\",\"{jsonifiedMetadata}\",\"{jsonifiedEmbedding}\",{isoFormattedDate}";
    }
}

public class KustoMemoryStore : IMemoryStore
{
    private string m_database;
    private static ClientRequestProperties GetClientRequestProperties() => new()
    {
        Application = "SemanticKernel",
    };

    private readonly ICslQueryProvider m_queryClient;
    private readonly ICslAdminProvider m_adminClient;

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

    public KustoMemoryStore(KustoConnectionStringBuilder kcsb, string database)
    {
        this.m_database = database;
        this.m_queryClient = KustoClientFactory.CreateCslQueryProvider(kcsb);
        this.m_adminClient = KustoClientFactory.CreateCslAdminProvider(kcsb);
    }

    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        await this.InitializeVectorFunctionsAsync().ConfigureAwait(false);

        using var resp = await this.m_adminClient
            .ExecuteControlCommandAsync(
                this.m_database,
                CslCommandGenerator.GenerateTableCreateCommand(new TableSchema(GetTableName(collectionName), s_collectionColumns)),
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }

    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using var resp = await this.m_adminClient
            .ExecuteControlCommandAsync(
                this.m_database,
                CslCommandGenerator.GenerateTableDropCommand(GetTableName(collectionName)),
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }

    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var result = await this.m_adminClient
            .ExecuteControlCommandAsync<TablesShowCommandResult>(
                this.m_database,
                CslCommandGenerator.GenerateTablesShowCommand() + $" | where TableName == '{GetTableName(collectionName)}'",
                GetClientRequestProperties()
            ).ConfigureAwait(false);

        return result.Count() == 1;
    }

    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var result = this.GetBatchAsync(collectionName, new[] { key }, withEmbedding, cancellationToken);
        return await result.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        var inClauseValue = string.Join(',', keys.Select(k => $"'{k}'"));
        var query = $"{this.GetBaseQuery(collectionName)} " +
            $"| where Key in ({inClauseValue}) " +
            $"| project " +
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
            // easiest way to ingore embeddings
            query += " | extend Embedding = ''";
        }

        using var reader = await this.m_queryClient
            .ExecuteQueryAsync(
                this.m_database,
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

    public async IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default)
    {
        var result = await this.m_adminClient
            .ExecuteControlCommandAsync<TablesShowCommandResult>(
                this.m_database,
                CslCommandGenerator.GenerateTablesShowCommand() + $" | where TableName startswith '{c_collectionPrefix}'",
                GetClientRequestProperties()
            ).ConfigureAwait(false);

        foreach (var item in result)
        {
            yield return GetCollectionName(item.TableName);
        }
    }

    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false, CancellationToken cancellationToken = default)
    {
        var result = this.GetNearestMatchesAsync(collectionName, embedding, 1, minRelevanceScore, withEmbedding, cancellationToken);
        return await result.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, CancellationToken cancellationToken = default)
    {
        var similiaryQuery = $"{this.GetBaseQuery(collectionName)} | extend similarity=series_cosine_similarity_fl('{KustoSerializer.SerializeEmbedding(embedding)}', {s_collectionColumns[2].Name}, 1, 1)";

        if (minRelevanceScore != 0)
        {
            similiaryQuery += $" | where similarity > {minRelevanceScore}";
        }

        similiaryQuery += $" | top {limit} by similarity desc";
        // reorder to make it easier to ignore the embedding (key, metadata, timestamp, similarity, embedding
        // Using tostring to make it easier to parse the result. There are probably better ways we should explore
        similiaryQuery += $"| project " +
            // Key
            $"{s_collectionColumns[0].Name}, " +
            // Metadata
            $"{s_collectionColumns[1].Name}=tostring({s_collectionColumns[1].Name}), " +
            // Timestamp
            $"{s_collectionColumns[3].Name}, " +
            $"similarity, " +
            // Embedding
            $"{s_collectionColumns[2].Name}=tostring({s_collectionColumns[2].Name})";

        if (!withEmbeddings)
        {
            similiaryQuery += $" | project-away {s_collectionColumns[2].Name} ";
        }

        using var reader = await this.m_queryClient
            .ExecuteQueryAsync(
                this.m_database,
                similiaryQuery,
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

    public Task RemoveAsync(string collectionName, string key, CancellationToken cancellationToken = default) => this.RemoveBatchAsync(collectionName, new[] { key }, cancellationToken);

    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default)
    {
        if (keys != null)
        {
            var keysString = string.Join(',', keys.Select(k => $"'{k}'"));
            using var resp = await this.m_adminClient
                .ExecuteControlCommandAsync(
                    this.m_database,
                    CslCommandGenerator.GenerateDeleteTableRecordsCommand(GetTableName(collectionName), $"{GetTableName(collectionName)} | where Key in ({keysString})"),
                    GetClientRequestProperties()
                ).ConfigureAwait(false);
        }
    }

    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancellationToken = default)
    {
        var result = this.UpsertBatchAsync(collectionName, new[] { record }, cancellationToken);
        return await result.FirstOrDefaultAsync(cancellationToken).ConfigureAwait(false);
    }

    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records, CancellationToken cancellationToken = default)
    {
        // Upserts don't exist in Kusto, as it is an append only store.
        // However, since we have an easy PK, we can just insert a new record, as our query always picks the latest row of that PK.
        // An intresting scenario is deletion after a lot of "Upserts". This could be a heavy operation, as in theory there could be many old version that we now need to remove.
        // Plus, deleting those records is a "soft delete" operation.
        // For simplicty purposes (and under the assumption that in most systems, upserts are rare), we will ignore the potential build-up of "garbage" records,
        // as Kusto is generally good with large amounts of data.

        var inlineIngestionCommand = $".ingest inline into table {GetTableName(collectionName)} <|\n";

        var recordsAsCsvString = "";
        var keys = new List<string>();
        var recordsAsList = records.ToList();
        for (var i = 0; i < recordsAsList.Count; i++)
        {
            var record = recordsAsList[i];
            record.Key = record.Metadata.Id;
            keys.Add(record.Key);
            recordsAsCsvString += $"{new KustoMemoryRecord(record).ToCsvString()}";
            // if not last element, add a new line
            if (i != recordsAsList.Count - 1)
            {
                recordsAsCsvString += "\n";
            }
        }

        var command = inlineIngestionCommand + recordsAsCsvString;
        await this.m_adminClient
            .ExecuteControlCommandAsync(
                m_database,
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
        // Kusto is an append only store. Although deletions are possible, they are highly discourged,
        //  and should only be used in rare cases (see: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/concepts/data-soft-delete#use-cases).
        // As such, the recommended approach for dealing with row updates is versioning. An easy way to achieve this is by using the ingestion time of the record (insertion time).
        return $"{GetTableName(collection)} | summarize arg_max(ingestion_time(), *) by {s_collectionColumns[0].Name} ";
    }

    private async Task InitializeVectorFunctionsAsync()
    {
        var resp = await this.m_adminClient
            .ExecuteControlCommandAsync<FunctionShowCommandResult>(
                this.m_database,
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
