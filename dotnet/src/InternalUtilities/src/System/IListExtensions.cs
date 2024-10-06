// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

[ExcludeFromCodeCoverage]
internal static class IListExtensions
{
    /// <summary>
    /// Adds a range of elements from the specified <see cref="IEnumerable{T}"/> source to the target <see cref="IList{T}"/>.
    /// </summary>
    /// <typeparam name="T">The type of elements in the list.</typeparam>
    /// <param name="target">The target <see cref="IList{T}"/> to add elements to.</param>
    /// <param name="source">The source <see cref="IEnumerable{T}"/> containing elements to add to the target <see cref="IList{T}"/>.</param>
    internal static void AddRange<T>(this IList<T> target, IEnumerable<T> source)
    {
        Debug.Assert(target is not null);
        Debug.Assert(source is not null);

        if (target is List<T> list)
        {
            list.AddRange(source);
        }
        else
        {
            foreach (var item in source!)
            {
                target!.Add(item);
            }
        }
    }
}
