// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extensions for configuring <see cref="LoggingVectorStoreRecordCollection{TKey, TRecord}"/> instances.</summary>
[Experimental("SKEXP0020")]
public static class LoggingVectorStoreRecordCollectionBuilderExtensions
{
    /// <summary>Adds logging to the vector store record collection pipeline.</summary>
    /// <param name="builder">The <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/>.</param>
    /// <param name="loggerFactory">
    /// An optional <see cref="ILoggerFactory"/> used to create a logger with which logging should be performed.
    /// If not supplied, a required instance will be resolved from the service provider.
    /// </param>
    /// <returns>The <paramref name="builder"/>.</returns>
    public static VectorStoreRecordCollectionBuilder<TKey, TRecord> UseLogging<TKey, TRecord>(
        this VectorStoreRecordCollectionBuilder<TKey, TRecord> builder,
        ILoggerFactory? loggerFactory = null) where TKey : notnull
    {
        return builder.Use((innerCollection, services) =>
        {
            loggerFactory ??= services.GetRequiredService<ILoggerFactory>();

            if (loggerFactory == NullLoggerFactory.Instance)
            {
                return innerCollection;
            }

            return new LoggingVectorStoreRecordCollection<TKey, TRecord>(innerCollection, loggerFactory.CreateLogger(typeof(LoggingVectorStoreRecordCollection<TKey, TRecord>)));
        });
    }
}
