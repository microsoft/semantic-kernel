// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a Kusto database.
/// </summary>
/// <remarks>The embedded data is saved to the Kusto database specified in the constructor.
/// Similarity search capability is provided through a cosine similarity function (added on first collection creation). Use Kusto's "Table" to implement "Collection".
/// </remarks>
public class KustoMemoryStore : IMemoryStore, IDisposable
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KustoMemoryStore"/> class.
    /// </summary>
    /// <param name="cslAdminProvider">Kusto Admin Client.</param>
    /// /// <param name="cslQueryProvider">Kusto Query Client.</param>
    /// <param name="database">The database used for the tables.</param>
    public KustoMemoryStore(ICslAdminProvider cslAdminProvider, ICslQueryProvider cslQueryProvider, string database)
    {
        this._database = database;
        this._queryClient = cslQueryProvider;
        this._adminClient = cslAdminProvider;

        this._initialized = false;
        this._disposer = new Disposer(nameof(KustoMemoryStore), nameof(KustoMemoryStore));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KustoMemoryStore"/> class.
    /// </summary>
    /// <param name="builder">Kusto Connection String Builder.</param>
    /// <param name="database">The database used for the tables.</param>
    public KustoMemoryStore(KustoConnectionStringBuilder builder, string database) : this(KustoClientFactory.CreateCslAdminProvider(builder), KustoClientFactory.CreateCslQueryProvider(builder), database)
    {
        // We created them, we dispose them
        this._disposer.Add(this._queryClient);
        this._disposer.Add(this._adminClient);
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        this.InitializeVectorFunctions();

        using var resp = await this._adminClient
            .ExecuteControlCommandAsync(
                this._database,
                CslCommandGenerator.GenerateTableCreateCommand(new TableSchema(GetTableName(collectionName, normalized: false), s_collectionColumns)),
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        using var resp = await this._adminClient
            .ExecuteControlCommandAsync(
                this._database,
                CslCommandGenerator.GenerateTableDropCommand(GetTableName(collectionName, normalized: false)),
                GetClientRequestProperties()
            ).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancellationToken = default)
    {
        var command = CslCommandGenerator.GenerateTablesShowCommand() + $" | where TableName == '{GetTableName(collectionName, normalized: false)}' | project TableName";
        var result = await this._adminClient
            .ExecuteControlCommandAsync<TablesShowCommandResult>(
                this._database,
                command,
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
            $"{KeyColumn.Name}, " +
            $"{MetadataColumn.Name}=tostring({MetadataColumn.Name}), " +
            $"{TimestampColumn.Name}, " +
            $"{EmbeddingColumn.Name}=tostring({EmbeddingColumn.Name})";

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
            DateTime? timestamp = null;
            try
            {
                reader.GetDateTime(2);
            }
            catch (InvalidCastException)
            {
                // timestamp is null or wrong format
            }
            var embedding = withEmbeddings ? reader.GetString(3) : default;

            var kustoRecord = new KustoMemoryRecord(key, metadata, embedding, timestamp);

            yield return kustoRecord.ToMemoryRecord();
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var result = await this._adminClient
            .ExecuteControlCommandAsync<TablesShowCommandResult>(
                this._database,
                CslCommandGenerator.GenerateTablesShowCommand(),
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
        this.InitializeVectorFunctions();

        var similarityQuery = $"{this.GetBaseQuery(collectionName)} | extend similarity=series_cosine_similarity_fl('{KustoSerializer.SerializeEmbedding(embedding)}', {EmbeddingColumn.Name}, 1, 1)";

        if (minRelevanceScore != 0)
        {
            similarityQuery += $" | where similarity > {minRelevanceScore}";
        }

        similarityQuery += $" | top {limit} by similarity desc";
        // reorder to make it easier to ignore the embedding (key, metadata, timestamp, similarity, embedding
        // Using tostring to make it easier to parse the result. There are probably better ways we should explore
        similarityQuery += "| project " +
            // Key
            $"{KeyColumn.Name}, " +
            // Metadata
            $"{MetadataColumn.Name}=tostring({MetadataColumn.Name}), " +
            // Timestamp
            $"{TimestampColumn.Name}, " +
            "similarity, " +
            // Embedding
            $"{EmbeddingColumn.Name}=tostring({EmbeddingColumn.Name})";

        if (!withEmbeddings)
        {
            similarityQuery += $" | project-away {EmbeddingColumn.Name} ";
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
            DateTime? timestamp = null;
            try
            {
                timestamp = reader.GetDateTime(2);
            }
            catch (InvalidCastException)
            {
                // timestamp is null or wrong format
            }

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

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._disposer.Dispose();
        }
    }

    #endregion protected ================================================================================

    #region private ================================================================================

    private Disposer _disposer;
    private object _lock = new();

    private string _database;

    private static ClientRequestProperties GetClientRequestProperties() => new()
    {
        Application = Telemetry.HttpUserAgent,
    };

    private readonly ICslQueryProvider _queryClient;
    private readonly ICslAdminProvider _adminClient;
    private bool _initialized;
    private static ColumnSchema KeyColumn = new("Key", typeof(string).FullName);
    private static ColumnSchema MetadataColumn = new("Metadata", typeof(object).FullName);
    private static ColumnSchema EmbeddingColumn = new("Embedding", typeof(object).FullName);
    private static ColumnSchema TimestampColumn = new("Timestamp", typeof(DateTime).FullName);

    private static readonly ColumnSchema[] s_collectionColumns = new ColumnSchema[]
    {
        KeyColumn,
        MetadataColumn,
        EmbeddingColumn,
        TimestampColumn
    };

    // Kusto escaping rules for table names: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/schema-entities/entity-names#identifier-quoting
    private static string GetTableName(string collectionName, bool normalized = true) => normalized ? CslSyntaxGenerator.NormalizeTableName(collectionName) : collectionName;
    // Kusto escaping rules for table names: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/schema-entities/entity-names#identifier-quoting
    private static string GetCollectionName(string tableName) => tableName.Replace("['", "").Replace("']", "");

    private string GetBaseQuery(string collection)
    {
        // Kusto is an append-only store. Although deletions are possible, they are highly discourged,
        // and should only be used in rare cases (see: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/concepts/data-soft-delete#use-cases).
        // As such, the recommended approach for dealing with row updates is versioning.
        // An easy way to achieve this is by using the ingestion time of the record (insertion time).
        return $"{GetTableName(collection)} | summarize arg_max(ingestion_time(), *) by {KeyColumn.Name} ";
    }

    private void InitializeVectorFunctions()
    {
        if (!this._initialized)
        {
            // We want to be nice and only initialize the functions once.
            // It won't hurt to run this code twice (.create-or-alter is basiccly "create if not exists"), but it's a waste of resources.
            lock (this._lock)
            {
                if (!this._initialized)
                {
                    var resp = this._adminClient
                        .ExecuteControlCommand<FunctionShowCommandResult>(
                            this._database,
                            ".create-or-alter function with (docstring = 'Calculate the Cosine similarity of 2 numerical arrays',folder = 'Vector') series_cosine_similarity_fl(vec1:dynamic,vec2:dynamic,vec1_size:real=real(null),vec2_size:real=real(null)) {" +
                            "  let dp = series_dot_product(vec1, vec2);" +
                            "  let v1l = iff(isnull(vec1_size), sqrt(series_dot_product(vec1, vec1)), vec1_size);" +
                            "  let v2l = iff(isnull(vec2_size), sqrt(series_dot_product(vec2, vec2)), vec2_size);" +
                            "  dp/(v1l*v2l)" +
                            "}",
                            GetClientRequestProperties()
                        );
                    this._initialized = true;
                }
            }
        }
    }

    #endregion private ================================================================================
}
