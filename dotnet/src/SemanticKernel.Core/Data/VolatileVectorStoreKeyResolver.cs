﻿// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Delegate that describes a function that given a record, finds the record key and returns it.
/// </summary>
/// <param name="record">The record to look up the key for.</param>
/// <returns>The record key.</returns>
[Experimental("SKEXP0001")]
public delegate TKey? VolatileVectorStoreKeyResolver<TKey, TRecord>(TRecord record)
    where TKey : notnull
    where TRecord : class;
