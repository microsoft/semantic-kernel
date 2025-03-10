// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extensions for configuring <see cref="LoggingVectorStore"/> instances.</summary>
[Experimental("SKEXP0020")]
public static class LoggingVectorStoreBuilderExtensions
{
    /// <summary>Adds logging to the vector store pipeline.</summary>
    /// <param name="builder">The <see cref="VectorStoreBuilder"/>.</param>
    /// <param name="loggerFactory">
    /// An optional <see cref="ILoggerFactory"/> used to create a logger with which logging should be performed.
    /// If not supplied, a required instance will be resolved from the service provider.
    /// </param>
    /// <returns>The <paramref name="builder"/>.</returns>
    public static VectorStoreBuilder UseLogging(
        this VectorStoreBuilder builder,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(builder);

        return builder.Use((innerStore, services) =>
        {
            loggerFactory ??= services.GetRequiredService<ILoggerFactory>();

            if (loggerFactory == NullLoggerFactory.Instance)
            {
                return innerStore;
            }

            return new LoggingVectorStore(innerStore, loggerFactory.CreateLogger(typeof(LoggingVectorStore)));
        });
    }
}
