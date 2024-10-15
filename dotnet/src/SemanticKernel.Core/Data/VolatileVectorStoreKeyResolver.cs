// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Delegate that describes a function that given a record, finds the record key and returns it.
/// </summary>
/// <param name="record">The record to look up the key for.</param>
/// <returns>The record key.</returns>
[Obsolete("This has been replaced by InMemoryVectorStoreKeyResolver in the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
public delegate TKey? VolatileVectorStoreKeyResolver<TKey, TRecord>(TRecord record)
    where TKey : notnull;
