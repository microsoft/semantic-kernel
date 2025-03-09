// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for working with <see cref="IKeywordHybridSearch{TRecord}"/> in the context of <see cref="KeywordHybridSearchBuilder{TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public static class KeywordHybridSearchBuilderExtensions
{
    /// <summary>Creates a new <see cref="KeywordHybridSearchBuilder{TRecord}"/> using <paramref name="innerSearch"/> as its inner search.</summary>
    /// <param name="innerSearch">The search to use as the inner search.</param>
    /// <returns>The new <see cref="KeywordHybridSearchBuilder{TRecord}"/> instance.</returns>
    /// <remarks>
    /// This method is equivalent to using the <see cref="KeywordHybridSearchBuilder{TRecord}"/> constructor directly,
    /// specifying <paramref name="innerSearch"/> as the inner search.
    /// </remarks>
    public static KeywordHybridSearchBuilder<TRecord> AsBuilder<TRecord>(this IKeywordHybridSearch<TRecord> innerSearch)
    {
        return new KeywordHybridSearchBuilder<TRecord>(innerSearch);
    }
}
