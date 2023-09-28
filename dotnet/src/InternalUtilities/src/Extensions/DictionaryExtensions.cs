// Copyright (c) Microsoft. All rights reserved.
#pragma warning restore IDE0130

using System.Collections.Generic;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Extensions;
/// <summary>
/// Dictionary extension methods.
/// </summary>
internal static class DictionaryExtensions
{
    /// <summary>Gets or adds a value to the dictionary.</summary>
    /// <typeparam name="TKey">The type of the name.</typeparam>
    /// <typeparam name="TValue">The type of the value.</typeparam>
    /// <param name="dictionary">The dictionary.</param>
    /// <param name="key">The name.</param>
    /// <param name="value">The value.</param>
    /// <returns>The final value.</returns>
    public static TValue? GetOrAdd<TKey, TValue>(this IDictionary<TKey, TValue> dictionary, TKey key, TValue value)
    {
        if (dictionary.TryGetValue(key, out TValue? foundValue))
        {
            return foundValue;
        }

        dictionary[key] = value;
        return value;
    }
}
