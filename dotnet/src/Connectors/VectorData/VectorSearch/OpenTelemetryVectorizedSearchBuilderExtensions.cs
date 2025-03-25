// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.SemanticKernel;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extensions for configuring <see cref="OpenTelemetryVectorizedSearch{TRecord}"/> instances.</summary>
[Experimental("SKEXP0020")]
public static class OpenTelemetryVectorizedSearchBuilderExtensions
{
    /// <summary>Adds OpenTelemetry support to the vectorized search pipeline, following the OpenTelemetry Semantic Conventions for database calls and systems.</summary>
    /// <remarks>
    /// The draft specification this follows is available at <see href="https://opentelemetry.io/docs/specs/semconv/database/"/>.
    /// The part of the specification is still experimental and subject to change; as such, the telemetry output is also subject to change.
    /// </remarks>
    /// <param name="builder">The <see cref="VectorizedSearchBuilder{TRecord}"/>.</param>
    /// <param name="sourceName">An optional source name that will be used on the telemetry data.</param>
    /// <returns>The <paramref name="builder"/>.</returns>
    public static VectorizedSearchBuilder<TRecord> UseOpenTelemetry<TRecord>(
        this VectorizedSearchBuilder<TRecord> builder,
        string? sourceName = null)
    {
        Verify.NotNull(builder);

        return builder.Use((innerSearch, services) =>
        {
            return new OpenTelemetryVectorizedSearch<TRecord>(innerSearch, sourceName);
        });
    }
}
