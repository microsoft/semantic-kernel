// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>Represents a delegating vectorized search that implements the OpenTelemetry Semantic Conventions for database calls and systems.</summary>
/// <remarks>
/// This class provides an implementation of the Semantic Conventions for database calls and systems v1.31, defined at <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
/// The part of the specification is still experimental and subject to change; as such, the telemetry output by this class is also subject to change.
/// </remarks>
[Experimental("SKEXP0020")]
public class OpenTelemetryVectorizedSearch<TRecord> : IVectorizedSearch<TRecord>, IDisposable
{
    private readonly ActivitySource _activitySource;
    private readonly Meter _meter;
    private readonly Histogram<double> _operationDurationHistogram;
    private readonly IVectorizedSearch<TRecord> _innerSearch;
    private readonly string? _vectorStoreSystemName;
    private readonly string? _databaseName;
    private readonly string? _collectionName;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenTelemetryVectorizedSearch{TRecord}"/> class.
    /// </summary>
    /// <param name="innerSearch">The underlying <see cref="IVectorizedSearch{TRecord}"/>.</param>
    /// <param name="sourceName">An optional source name that will be used on the telemetry data.</param>
    public OpenTelemetryVectorizedSearch(IVectorizedSearch<TRecord> innerSearch, string? sourceName = null)
    {
        this._innerSearch = innerSearch ?? throw new ArgumentNullException(nameof(innerSearch));

        if (this._innerSearch.GetService(typeof(VectorStoreRecordCollectionMetadata)) is VectorStoreRecordCollectionMetadata metadata)
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
    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(
        TVector vector,
        VectorSearchOptions<TRecord>? options = default,
        CancellationToken cancellationToken = default)
    {
        const string OperationName = "vectorized_search";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            this._collectionName,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerSearch.VectorizedSearchAsync(vector, options, cancellationToken));
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        _ = serviceType ?? throw new ArgumentNullException(nameof(serviceType));

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            this._innerSearch.GetService(serviceType, serviceKey);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
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
