// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace RepoUtils;

public static class EnumerableExtensions
{
    public static IEnumerable<List<TSource>> ChunkByAggregate<TSource, TAccumulate>(
        this IEnumerable<TSource> source,
        TAccumulate seed,
        Func<TAccumulate, TSource, TAccumulate> aggregator,
        Func<TAccumulate, int, bool> predicate)
    {
        using var enumerator = source.GetEnumerator();
        var aggregate = seed;
        var index = 0;
        var chunk = new List<TSource>();

        while (enumerator.MoveNext())
        {
            var current = enumerator.Current;

            aggregate = aggregator(aggregate, current);

            if (predicate(aggregate, index++))
            {
                chunk.Add(current);
            }
            else
            {
                if (chunk.Count > 0)
                {
                    yield return chunk;
                }

                chunk = new List<TSource>() { current };
                aggregate = aggregator(seed, current);
                index = 1;
            }
        }

        if (chunk.Count > 0)
        {
            yield return chunk;
        }
    }
}
