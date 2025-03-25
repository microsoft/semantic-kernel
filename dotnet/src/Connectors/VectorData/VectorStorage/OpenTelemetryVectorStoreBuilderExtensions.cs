// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extensions for configuring <see cref="OpenTelemetryVectorStore"/> instances.</summary>
[Experimental("SKEXP0020")]
public static class OpenTelemetryVectorStoreBuilderExtensions
{
    /// <summary>Adds OpenTelemetry support to the vector store pipeline, following the OpenTelemetry Semantic Conventions for database calls and systems.</summary>
    /// <remarks>
    /// The draft specification this follows is available at at <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
    /// The part of the specification is still experimental and subject to change; as such, the telemetry output is also subject to change.
    /// </remarks>
    /// <param name="builder">The <see cref="VectorStoreBuilder"/>.</param>
    /// <param name="sourceName">An optional source name that will be used on the telemetry data.</param>
    /// <returns>The <paramref name="builder"/>.</returns>
    public static VectorStoreBuilder UseOpenTelemetry(
        this VectorStoreBuilder builder,
        string? sourceName = null)
    {
        Verify.NotNull(builder);

        return builder.Use((innerStore, services) =>
        {
            return new OpenTelemetryVectorStore(innerStore, sourceName);
        });
    }
}
