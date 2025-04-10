// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Interface for mapping between a <see cref="ITextSearch" /> implementation result value, and a <see cref="string" /> instance.
/// </summary>
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

/// <summary>
/// Delegate to map from an <see cref="object"/> which represents a result value associated with a <see cref="ITextSearch" /> implementation
/// to a a <see cref="string" /> instance.
/// </summary>
/// <param name="result">The result value to map.</param>
/// <returns>A string value.</returns>
public delegate string MapFromResultToString(object result);

/// <summary>
/// Default implementation of <see cref="ITextSearchStringMapper" /> that use the <see cref="MapFromResultToString" /> delegate.
/// </summary>
/// <param name="mapFromResultToString">MapFromResultToString delegate</param>
public class TextSearchStringMapper(MapFromResultToString mapFromResultToString) : ITextSearchStringMapper
{
    /// <inheritdoc />
    public string MapFromResultToString(object result)
    {
        return mapFromResultToString(result);
    }
}
