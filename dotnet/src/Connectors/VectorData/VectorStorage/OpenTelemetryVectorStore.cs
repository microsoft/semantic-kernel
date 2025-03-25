// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Diagnostics.Metrics;
using System.Threading;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Represents a delegating vector store that implements the OpenTelemetry Semantic Conventions for database calls and systems.</summary>
/// <remarks>
/// This class provides an implementation of the Semantic Conventions for database calls and systems v1.31, defined at <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
/// The part of the specification is still experimental and subject to change; as such, the telemetry output by this class is also subject to change.
/// </remarks>
[Experimental("SKEXP0020")]
public class OpenTelemetryVectorStore : IVectorStore, IDisposable
{
    private readonly ActivitySource _activitySource;
    private readonly Meter _meter;
    private readonly Histogram<double> _operationDurationHistogram;
    private readonly IVectorStore _innerStore;
    private readonly string? _vectorStoreSystemName;
    private readonly string? _databaseName;
    private readonly string _telemetrySourceName;

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenTelemetryVectorStore"/> class.
    /// </summary>
    /// <param name="innerStore">The underlying <see cref="IVectorStore"/>.</param>
    /// <param name="sourceName">An optional source name that will be used on the telemetry data.</param>
    public OpenTelemetryVectorStore(IVectorStore innerStore, string? sourceName = null)
    {
        this._innerStore = innerStore ?? throw new ArgumentNullException(nameof(innerStore));

        if (this._innerStore.GetService(typeof(VectorStoreMetadata)) is VectorStoreMetadata metadata)
        {
            this._vectorStoreSystemName = metadata.VectorStoreSystemName;
            this._databaseName = metadata.DatabaseName;
        }

        this._telemetrySourceName = OpenTelemetryConstants.GetSourceNameOrDefault(sourceName);

        this._activitySource = new ActivitySource(this._telemetrySourceName);
        this._meter = new Meter(this._telemetrySourceName);

        this._operationDurationHistogram = this._meter.CreateHistogram<double>(
            OpenTelemetryConstants.DbOperationDurationMetricName,
            OpenTelemetryConstants.SecondsUnit,
            OpenTelemetryConstants.DbOperationDurationMetricDescription);
    }

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
        => new OpenTelemetryVectorStoreRecordCollection<TKey, TRecord>(
            this._innerStore.GetCollection<TKey, TRecord>(name, vectorStoreRecordDefinition),
            this._telemetrySourceName);

    /// <inheritdoc/>
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        const string OperationName = "list_collection_names";

        return TelemetryHelpers.RunOperationAsync(
            this._activitySource,
            OperationName,
            null,
            this._databaseName,
            this._vectorStoreSystemName,
            this._operationDurationHistogram,
            () => this._innerStore.ListCollectionNamesAsync(cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            this._innerStore.GetService(serviceType, serviceKey);
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
