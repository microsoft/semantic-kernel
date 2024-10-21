// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
using System.Diagnostics.CodeAnalysis;
=======
using System;
>>>>>>> main

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Delegate that describes a function that given a record, finds the record key and returns it.
/// </summary>
/// <param name="record">The record to look up the key for.</param>
/// <returns>The record key.</returns>
<<<<<<< HEAD
[Experimental("SKEXP0001")]
=======
[Obsolete("This has been replaced by InMemoryVectorStoreKeyResolver in the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
>>>>>>> main
public delegate TKey? VolatileVectorStoreKeyResolver<TKey, TRecord>(TRecord record)
    where TKey : notnull;
