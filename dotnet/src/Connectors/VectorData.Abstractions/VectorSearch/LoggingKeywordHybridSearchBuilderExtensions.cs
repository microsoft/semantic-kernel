// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extensions for configuring <see cref="LoggingKeywordHybridSearch{TRecord}"/> instances.</summary>
[Experimental("SKEXP0020")]
public static class LoggingKeywordHybridSearchBuilderExtensions
{
    /// <summary>Adds logging to the keyword hybrid search pipeline.</summary>
    /// <param name="builder">The <see cref="KeywordHybridSearchBuilder{TRecord}"/>.</param>
    /// <param name="loggerFactory">
    /// An optional <see cref="ILoggerFactory"/> used to create a logger with which logging should be performed.
    /// If not supplied, a required instance will be resolved from the service provider.
    /// </param>
    /// <returns>The <paramref name="builder"/>.</returns>
    public static KeywordHybridSearchBuilder<TRecord> UseLogging<TRecord>(
        this KeywordHybridSearchBuilder<TRecord> builder,
        ILoggerFactory? loggerFactory = null)
    {
        return builder.Use((innerSearch, services) =>
        {
            loggerFactory ??= services.GetRequiredService<ILoggerFactory>();

            if (loggerFactory == NullLoggerFactory.Instance)
            {
                return innerSearch;
            }

            return new LoggingKeywordHybridSearch<TRecord>(innerSearch, loggerFactory.CreateLogger(typeof(LoggingKeywordHybridSearch<TRecord>)));
        });
    }
}
