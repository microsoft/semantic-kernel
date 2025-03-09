// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for working with <see cref="IVectorizedSearch{TRecord}"/> in the context of <see cref="VectorizedSearchBuilder{TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorizedSearchBuilderExtensions
{
    /// <summary>Creates a new <see cref="VectorizedSearchBuilder{TRecord}"/> using <paramref name="innerSearch"/> as its inner search.</summary>
    /// <param name="innerSearch">The search to use as the inner search.</param>
    /// <returns>The new <see cref="VectorizedSearchBuilder{TRecord}"/> instance.</returns>
    /// <remarks>
    /// This method is equivalent to using the <see cref="VectorizedSearchBuilder{TRecord}"/> constructor directly,
    /// specifying <paramref name="innerSearch"/> as the inner search.
    /// </remarks>
    public static VectorizedSearchBuilder<TRecord> AsBuilder<TRecord>(this IVectorizedSearch<TRecord> innerSearch)
    {
        return new VectorizedSearchBuilder<TRecord>(innerSearch);
    }
}
