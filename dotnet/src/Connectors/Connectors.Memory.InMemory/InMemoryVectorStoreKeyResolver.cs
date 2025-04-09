// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Delegate that describes a function that given a record, finds the record key and returns it.
/// </summary>
/// <param name="record">The record to look up the key for.</param>
/// <returns>The record key.</returns>
public delegate TKey? InMemoryVectorStoreKeyResolver<TKey, TRecord>(TRecord record)
    where TKey : notnull;
