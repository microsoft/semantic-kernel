// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData;

/// <summary>Provides extension methods for working with <see cref="IVectorStore"/> in the context of <see cref="VectorStoreBuilder"/>.</summary>
[Experimental("SKEXP0020")]
public static class VectorStoreBuilderExtensions
{
    /// <summary>Creates a new <see cref="VectorStoreBuilder"/> using <paramref name="innerStore"/> as its inner store.</summary>
    /// <param name="innerStore">The store to use as the inner store.</param>
    /// <returns>The new <see cref="VectorStoreBuilder"/> instance.</returns>
    /// <remarks>
    /// This method is equivalent to using the <see cref="VectorStoreBuilder"/> constructor directly,
    /// specifying <paramref name="innerStore"/> as the inner store.
    /// </remarks>
    public static VectorStoreBuilder AsBuilder(this IVectorStore innerStore)
    {
        return new VectorStoreBuilder(innerStore);
    }
}
