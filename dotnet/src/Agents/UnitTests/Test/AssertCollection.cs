// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.Test;

internal static class AssertCollection
{
    public static void Equal<T>(IReadOnlyList<T>? source, IReadOnlyList<T>? target, Func<T, object?>? adapter = null)
    {
        if (source == null)
        {
            Assert.Null(target);
            return;
        }

        Assert.NotNull(target);
        Assert.Equal(source.Count, target.Count);

        adapter ??= (x) => x;

        for (int i = 0; i < source.Count; i++)
        {
            Assert.Equal(adapter(source[i]), adapter(target[i]));
        }
    }

    public static void Equal<TKey, TValue>(IReadOnlyDictionary<TKey, TValue>? source, IReadOnlyDictionary<TKey, TValue>? target)
    {
        if (source == null)
        {
            Assert.Null(target);
            return;
        }

        Assert.NotNull(target);
        Assert.Equal(source.Count, target.Count);

        foreach ((TKey key, TValue value) in source)
        {
            Assert.True(target.TryGetValue(key, out TValue? targetValue));
            Assert.Equal(value, targetValue);
        }
    }
}
