// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Delegate that describes a function that given a vector name and a record, finds the vector in the record and returns it.
/// </summary>
/// <param name="vectorName">The name of the vector to find.</param>
/// <param name="record">The record that contains the vector to look up.</param>
/// <returns>The named vector from the record.</returns>
public delegate object? InMemoryVectorStoreVectorResolver<TRecord>(string vectorName, TRecord record);
