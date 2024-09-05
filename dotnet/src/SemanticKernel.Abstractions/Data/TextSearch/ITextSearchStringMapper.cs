// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for mapping between a <see cref="ITextSearch" /> implementation result value, and a <see cref="string" /> instance.
/// </summary>
[Experimental("SKEXP0001")]
public interface ITextSearchStringMapper
{
    /// <summary>
    /// Map from an <see cref="object"/> which represents a result value associated with a <see cref="ITextSearch" /> implementation
    /// to a a <see cref="string" /> instance.
    /// </summary>
    /// <param name="result">The result value to map.</param>
    /// <returns>A string value.</returns>
    string MapFromResultToString(object result);
}
