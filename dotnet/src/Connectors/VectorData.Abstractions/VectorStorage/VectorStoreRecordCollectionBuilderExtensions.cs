// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for working with <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> in the context of <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorStoreRecordCollectionBuilderExtensions
{
    /// <summary>Creates a new <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> using <paramref name="innerCollection"/> as its inner collection.</summary>
    /// <param name="innerCollection">The collection to use as the inner collection.</param>
    /// <returns>The new <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> instance.</returns>
    /// <remarks>
    /// This method is equivalent to using the <see cref="VectorStoreRecordCollectionBuilder{TKey, TRecord}"/> constructor directly,
    /// specifying <paramref name="innerCollection"/> as the inner collection.
    /// </remarks>
    public static VectorStoreRecordCollectionBuilder<TKey, TRecord> AsBuilder<TKey, TRecord>(this IVectorStoreRecordCollection<TKey, TRecord> innerCollection) where TKey : notnull
    {
        return new VectorStoreRecordCollectionBuilder<TKey, TRecord>(innerCollection);
    }
}
