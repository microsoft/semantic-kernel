// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.Memory.SqlServer;

public interface ISqlServerClient
{
    Task CreateCollectionAsync(string collectionName, CancellationToken cancellationToken = default);
    Task CreateTables(CancellationToken cancellationToken);
    Task DeleteAsync(string collectionName, string key, CancellationToken cancellationToken = default);
    Task DeleteBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancellationToken = default);
    Task DeleteCollectionAsync(string collectionName, CancellationToken cancellationToken = default);
    Task<bool> DoesCollectionExistsAsync(string collectionName, CancellationToken cancellationToken = default);
    IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancellationToken = default);
    IAsyncEnumerable<(SqlServerMemoryEntry, double)> GetNearestMatchesAsync(string collectionName, string embedding, int limit, double minRelevanceScore = 0, bool withEmbeddings = false, [EnumeratorCancellation] CancellationToken cancellationToken = default);
    Task<SqlServerMemoryEntry?> ReadAsync(string collectionName, string key, bool withEmbeddings = false, CancellationToken cancellationToken = default);
    IAsyncEnumerable<SqlServerMemoryEntry> ReadBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false, CancellationToken cancellationToken = default);
    Task UpsertAsync(string collectionName, string key, string? metadata, string embedding, DateTimeOffset? timestamp, CancellationToken cancellationToken = default);
}
