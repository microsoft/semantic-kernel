// Copyright (c) Microsoft. All rights reserved.

namespace VectorStoreRAG;

/// <summary>
/// Class for generating unique keys via a provided function.
/// </summary>
/// <typeparam name="TKey">The type of key to generate.</typeparam>
/// <param name="generator">The function to generate the key with.</param>
internal sealed class UniqueKeyGenerator<TKey>(Func<TKey> generator)
    where TKey : notnull
{
    /// <summary>
    /// Generate a unique key.
    /// </summary>
    /// <returns>The unique key that was generated.</returns>
    public TKey GenerateKey() => generator();
}
