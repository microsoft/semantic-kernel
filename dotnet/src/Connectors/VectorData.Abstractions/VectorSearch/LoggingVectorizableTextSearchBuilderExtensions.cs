// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extensions for configuring <see cref="LoggingVectorizableTextSearch{TRecord}"/> instances.</summary>
[Experimental("SKEXP0020")]
public static class LoggingVectorizableTextSearchBuilderExtensions
{
    /// <summary>Adds logging to the vectorizable text search pipeline.</summary>
    /// <param name="builder">The <see cref="VectorizableTextSearchBuilder{TRecord}"/>.</param>
    /// <param name="loggerFactory">
    /// An optional <see cref="ILoggerFactory"/> used to create a logger with which logging should be performed.
    /// If not supplied, a required instance will be resolved from the service provider.
    /// </param>
    /// <returns>The <paramref name="builder"/>.</returns>
    public static VectorizableTextSearchBuilder<TRecord> UseLogging<TRecord>(
        this VectorizableTextSearchBuilder<TRecord> builder,
        ILoggerFactory? loggerFactory = null)
    {
        return builder.Use((innerSearch, services) =>
        {
            loggerFactory ??= services.GetRequiredService<ILoggerFactory>();

            if (loggerFactory == NullLoggerFactory.Instance)
            {
                return innerSearch;
            }

            return new LoggingVectorizableTextSearch<TRecord>(innerSearch, loggerFactory.CreateLogger(typeof(LoggingVectorizableTextSearch<TRecord>)));
        });
    }
}
