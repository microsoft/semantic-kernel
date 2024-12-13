﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

// Used for compatibility with System.Linq.Async Nuget pkg
namespace System.Linq;

[ExcludeFromCodeCoverage]
internal static class AsyncEnumerable
{
    public static IAsyncEnumerable<T> Empty<T>() => EmptyAsyncEnumerable<T>.Instance;

#pragma warning disable VSTHRD002 // Avoid problematic synchronous waits
    public static IEnumerable<T> ToEnumerable<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        var enumerator = source.GetAsyncEnumerator(cancellationToken);
        try
        {
            while (enumerator.MoveNextAsync().AsTask().GetAwaiter().GetResult())
            {
                yield return enumerator.Current;
            }
        }
        finally
        {
            enumerator.DisposeAsync().AsTask().GetAwaiter().GetResult();
        }
    }
#pragma warning restore VSTHRD002 // Avoid problematic synchronous waits

#pragma warning disable IDE1006 // Naming rule violation: Missing suffix: 'Async'
#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    public static async IAsyncEnumerable<T> ToAsyncEnumerable<T>(this IEnumerable<T> source)
    {
        foreach (var item in source)
        {
            yield return item;
        }
    }
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously
#pragma warning restore IDE1006 // Naming rule violation: Missing suffix: 'Async'

    public static async ValueTask<T?> FirstOrDefaultAsync<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            return item;
        }

        return default;
    }

    public static async ValueTask<T?> LastOrDefaultAsync<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        var last = default(T)!; // NB: Only matters when hasLast is set to true.
        var hasLast = false;

        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            hasLast = true;
            last = item;
        }

        return hasLast ? last! : default;
    }

    public static async ValueTask<List<T>> ToListAsync<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        var result = new List<T>();

        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            result.Add(item);
        }

        return result;
    }

    public static async ValueTask<bool> ContainsAsync<T>(this IAsyncEnumerable<T> source, T value)
    {
        await foreach (var item in source.ConfigureAwait(false))
        {
            if (EqualityComparer<T>.Default.Equals(item, value))
            {
                return true;
            }
        }

        return false;
    }

    public static async ValueTask<int> CountAsync<T>(this IAsyncEnumerable<T> source, CancellationToken cancellationToken = default)
    {
        int count = 0;
        await foreach (var _ in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            checked { count++; }
        }

        return count;
    }

    /// <summary>
    /// Determines whether any element of an async-enumerable sequence satisfies a condition.
    /// </summary>
    /// <typeparam name="TSource">The type of the elements in the source sequence.</typeparam>
    /// <param name="source">An async-enumerable sequence whose elements to apply the predicate to.</param>
    /// <param name="predicate">A function to test each element for a condition.</param>
    /// <param name="cancellationToken">The optional cancellation token to be used for cancelling the sequence at any time.</param>
    /// <returns>An async-enumerable sequence containing a single element determining whether any elements in the source sequence pass the test in the specified predicate.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="source"/> or <paramref name="predicate"/> is null.</exception>
    /// <remarks>The return type of this operator differs from the corresponding operator on IEnumerable in order to retain asynchronous behavior.</remarks>
    public static ValueTask<bool> AnyAsync<TSource>(this IAsyncEnumerable<TSource> source, Func<TSource, bool> predicate, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(source);
        Verify.NotNull(predicate);

        return Core(source, predicate, cancellationToken);

        static async ValueTask<bool> Core(IAsyncEnumerable<TSource> source, Func<TSource, bool> predicate, CancellationToken cancellationToken)
        {
            await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
            {
                if (predicate(item))
                {
                    return true;
                }
            }

            return false;
        }
    }

#pragma warning disable IDE1006 // Naming rule violation: Missing suffix: 'Async'

    /// <summary>
    /// Projects each element of an <see cref="IAsyncEnumerable{TSource}"/> into a new form by incorporating
    /// an asynchronous transformation function.
    /// </summary>
    /// <typeparam name="TSource">The type of the elements of the source sequence.</typeparam>
    /// <typeparam name="TResult">The type of the elements of the resulting sequence.</typeparam>
    /// <param name="source">An <see cref="IAsyncEnumerable{TSource}"/> to invoke a transform function on.</param>
    /// <param name="selector">
    /// A transform function to apply to each element. This function takes an element of
    /// type TSource and returns an element of type TResult.
    /// </param>
    /// <param name="cancellationToken">
    /// A CancellationToken to observe while iterating through the sequence.
    /// </param>
    /// <returns>
    /// An <see cref="IAsyncEnumerable{TResult}"/> whose elements are the result of invoking the transform
    /// function on each element of the original sequence.
    /// </returns>
    /// <exception cref="ArgumentNullException">Thrown when the source or selector is null.</exception>
    public static async IAsyncEnumerable<TResult> SelectAsync<TSource, TResult>(
       this IAsyncEnumerable<TSource> source,
       Func<TSource, TResult> selector,
       [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            yield return selector(item);
        }
    }

#pragma warning restore IDE1006 // Naming rule violation: Missing suffix: 'Async'

    private sealed class EmptyAsyncEnumerable<T> : IAsyncEnumerable<T>, IAsyncEnumerator<T>
    {
        public static readonly EmptyAsyncEnumerable<T> Instance = new();
        public IAsyncEnumerator<T> GetAsyncEnumerator(CancellationToken cancellationToken = default) => this;
        public ValueTask<bool> MoveNextAsync() => new(false);
        public T Current => default!;
        public ValueTask DisposeAsync() => default;
    }
}
