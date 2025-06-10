// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;

[ExcludeFromCodeCoverage]
internal static class EnumerableExtensions
{
    public static IEnumerable<TSource> TakeLast<TSource>(this IEnumerable<TSource> source, int count)
    {
        Debug.Assert(source is not null);

#if NETCOREAPP2_0_OR_GREATER || NETSTANDARD2_1_OR_GREATER
        return Enumerable.TakeLast(source, count);
#else
        return source.Skip(System.Math.Max(0, source.Count() - count));
#endif
    }
}
