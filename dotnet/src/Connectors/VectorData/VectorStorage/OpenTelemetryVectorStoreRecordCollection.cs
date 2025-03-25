// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Represents a delegating vector store record collection that implements the OpenTelemetry Semantic Conventions for database calls and systems.</summary>
/// <remarks>
/// This class provides an implementation of the Semantic Conventions for database calls and systems v1.31, defined at <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
/// The part of the specification is still experimental and subject to change; as such, the telemetry output by this class is also subject to change.
/// </remarks>
[Experimental("SKEXP0020")]
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix
public class OpenTelemetryVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>, IDisposable where TKey : notnull
#pragma warning restore CA1711 // Identifiers should not have incorrect suffix
{
    private readonly ActivitySource _activitySource;
    private readonly Meter _meter;
    private readonly Histogram<double> _operationDurationHistogram;
    private readonly IVectorStoreRecordCollection<TKey, TRecord> _innerCollection;
    private readonly string? _vectorStoreSystemName;
    private readonly string? _databaseName;
    private readonly string? _collectionName;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenTelemetryVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="innerCollection">The underlying <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="sourceName">An optional source name that will be used on the telemetry data.</param>
    public OpenTelemetryVectorStoreRecordCollection(IVectorStoreRecordCollection<TKey, TRecord> innerCollection, string? sourceName = null)
    {
        this._innerCollection = innerCollection ?? throw new ArgumentNullException(nameof(innerCollection));

        if (this._innerCollection.GetService(typeof(VectorStoreRecordCollectionMetadata)) is VectorStoreRecordCollectionMetadata metadata)
        {
            this._vectorStoreSystemName = metadata.VectorStoreSystemName;
            this._databaseName = metadata.DatabaseName;
            this._collectionName = metadata.CollectionName;
        }

        var telemetrySourceName = OpenTelemetryConstants.GetSourceNameOrDefault(sourceName);

        this._activitySource = new ActivitySource(telemetrySourceName);
        this._meter = new Meter(telemetrySourceName);

        this._operationDurationHistogram = this._meter.CreateHistogram<double>(
            OpenTelemetryConstants.DbOperationDurationMetricName,
            OpenTelemetryConstants.SecondsUnit,
            OpenTelemetryConstants.DbOperationDurationMetricDescription);
    }

    /// <inheritdoc/>
    [Obsolete("Use GetService(typeof(VectorStoreRecordCollectionMetadata)) to get an information about vector store record collection.")]
    public string CollectionName => this._innerCollection.CollectionName;

    /// <inheritdoc/>
    public Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "collection_exists";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.CollectionExistsAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "create_collection";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.CreateCollectionAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "create_collection_if_not_exists";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.CreateCollectionIfNotExistsAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        const string OperationName = "delete";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.DeleteAsync(key, cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        const string OperationName = "delete_batch";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.DeleteBatchAsync(keys, cancellationToken));
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "delete_collection";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.DeleteCollectionAsync(cancellationToken));
    }

    /// <inheritdoc/>
    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "get";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.GetAsync(key, options, cancellationToken));
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "get_batch";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.GetBatchAsync(keys, options, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        const string OperationName = "upsert";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.UpsertAsync(record, cancellationToken));
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        const string OperationName = "upsert_batch";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.UpsertBatchAsync(records, cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        const string OperationName = "vectorized_search";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerCollection.VectorizedSearchAsync(vector, options, cancellationToken));
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            this._innerCollection.GetService(serviceType, serviceKey);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    /// <summary>Provides a mechanism for releasing unmanaged resources.</summary>
    /// <param name="disposing"><see langword="true"/> if being called from <see cref="Dispose()"/>; otherwise, <see langword="false"/>.</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._activitySource.Dispose();
            this._meter.Dispose();
        }
    }
}
