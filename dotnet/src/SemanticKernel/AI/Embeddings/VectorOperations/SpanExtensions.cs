// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;

/// <summary>
/// Extension methods to convert from array and <see cref="Span{T}"/> to <see cref="ReadOnlySpan{T}"/>.
/// </summary>
internal static class SpanExtensions
{
    internal static ReadOnlySpan<TNumber> AsReadOnlySpan<TNumber>(this TNumber[] vector)
    {
        return new ReadOnlySpan<TNumber>(vector);
    }

    internal static ReadOnlySpan<TNumber> AsReadOnlySpan<TNumber>(this Span<TNumber> span)
    {
        return span;
    }
}
