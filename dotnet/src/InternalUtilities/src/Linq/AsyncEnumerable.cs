// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

#pragma warning disable IDE1006 // Naming Styles

// Used for compatibility with System.Linq.AsyncEnumerable Nuget pkg
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

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    public static async IAsyncEnumerable<T> ToAsyncEnumerable<T>(this IEnumerable<T> source)
    {
        foreach (var item in source)
        {
            yield return item;
        }
    }
#pragma warning restore CS1998 // Async method lacks 'await' operators and will run synchronously

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

    public static async IAsyncEnumerable<T> Cast<T>(this IAsyncEnumerable<object> source)
    {
        await foreach (var item in source.ConfigureAwait(false))
        {
            yield return (T)item;
        }
    }

    public static async IAsyncEnumerable<T> Reverse<T>(this IAsyncEnumerable<T> source, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        T[] results = await source.ToArrayAsync(cancellationToken).ConfigureAwait(false);
        for (int i = results.Length - 1; i >= 0; i--)
        {
            yield return results[i];
        }
    }

    public static async ValueTask<TSource> FirstAsync<TSource>(this IAsyncEnumerable<TSource> source, CancellationToken cancellationToken = default)
    {
        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            return item;
        }

        throw new InvalidOperationException("Sequence contains no elements");
    }

    public static async ValueTask<TSource> LastAsync<TSource>(this IAsyncEnumerable<TSource> source, CancellationToken cancellationToken = default)
    {
        var enumerator = source.GetAsyncEnumerator(cancellationToken);
        try
        {
            if (await enumerator.MoveNextAsync().ConfigureAwait(false))
            {
                var last = enumerator.Current;
                while (await enumerator.MoveNextAsync().ConfigureAwait(false))
                {
                    last = enumerator.Current;
                }

                return last;
            }

            throw new InvalidOperationException("Sequence contains no elements");
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    public static async ValueTask<TSource> SingleAsync<TSource>(this IAsyncEnumerable<TSource> source, CancellationToken cancellationToken = default)
    {
        var enumerator = source.GetAsyncEnumerator(cancellationToken);
        try
        {
            if (await enumerator.MoveNextAsync().ConfigureAwait(false))
            {
                var result = enumerator.Current;
                if (await enumerator.MoveNextAsync().ConfigureAwait(false))
                {
                    throw new InvalidOperationException("Sequence contains more than one element");
                }

                return result;
            }

            throw new InvalidOperationException("Sequence contains no elements");
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Determines whether any element of an async-enumerable sequence satisfies a condition.
    /// </summary>
    /// <typeparam name="TSource">The type of the elements in the source sequence.</typeparam>
    /// <param name="source">An async-enumerable sequence whose elements to apply the predicate to.</param>
    /// <param name="predicate">A function to test each element for a condition.</param>
    /// <param name="cancellationToken">The optional cancellation token to be used for cancelling the sequence at any time.</param>
    /// <returns>An async-enumerable sequence containing a single element determining whether any elements in the source sequence pass the test in the specified predicate.</returns>
    /// <remarks>The return type of this operator differs from the corresponding operator on IEnumerable in order to retain asynchronous behavior.</remarks>
    public static async ValueTask<bool> AnyAsync<TSource>(this IAsyncEnumerable<TSource> source, Func<TSource, bool> predicate, CancellationToken cancellationToken = default)
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

    /// <summary>
    /// Determines whether any element of an async-enumerable sequence satisfies a condition.
    /// </summary>
    /// <typeparam name="TSource">The type of the elements in the source sequence.</typeparam>
    /// <param name="source">An async-enumerable sequence whose elements to apply the predicate to.</param>
    /// <param name="cancellationToken">The optional cancellation token to be used for cancelling the sequence at any time.</param>
    /// <returns>An async-enumerable sequence containing a single element determining whether any elements in the source sequence pass the test in the specified predicate.</returns>
    /// <remarks>The return type of this operator differs from the corresponding operator on IEnumerable in order to retain asynchronous behavior.</remarks>
    public static async ValueTask<bool> AnyAsync<TSource>(this IAsyncEnumerable<TSource> source, CancellationToken cancellationToken = default)
    {
        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            return true;
        }

        return false;
    }

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
    public static async IAsyncEnumerable<TResult> Select<TSource, TResult>(
       this IAsyncEnumerable<TSource> source,
       Func<TSource, TResult> selector,
       [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var item in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            yield return selector(item);
        }
    }

    /// <summary>Sorts the elements of a sequence in ascending order.</summary>
    /// <typeparam name="TSource">The type of the elements of <paramref name="source"/>.</typeparam>
    /// <typeparam name="TKey">The type of the key returned by <paramref name="keySelector"/>.</typeparam>
    /// <param name="source">A sequence of values to order.</param>
    /// <param name="keySelector">A function to extract a key from an element.</param>
    /// <returns>An <see cref="IAsyncEnumerable{TElement}"/> whose elements are sorted according to a key.</returns>
    public static async IAsyncEnumerable<TSource> OrderBy<TSource, TKey>(this IAsyncEnumerable<TSource> source, Func<TSource, TKey> keySelector)
    {
        var results = await source.ToArrayAsync().ConfigureAwait(false);
        var keys = results.Select(keySelector).ToArray();
        Array.Sort(keys, results);
        foreach (var result in results)
        {
            yield return result;
        }
    }

    /// <summary>
    /// Creates an array from an async-enumerable sequence.
    /// </summary>
    /// <typeparam name="TSource">The type of the elements in the source sequence.</typeparam>
    /// <param name="source">The source async-enumerable sequence to get an array of elements for.</param>
    /// <param name="cancellationToken">The optional cancellation token to be used for cancelling the sequence at any time.</param>
    /// <returns>An async-enumerable sequence containing a single element with an array containing all the elements of the source sequence.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="source"/> is null.</exception>
    /// <remarks>The return type of this operator differs from the corresponding operator on IEnumerable in order to retain asynchronous behavior.</remarks>
    public static async ValueTask<TSource[]> ToArrayAsync<TSource>(this IAsyncEnumerable<TSource> source, CancellationToken cancellationToken = default)
    {
        List<TSource> results = [];
        await foreach (var result in source.WithCancellation(cancellationToken).ConfigureAwait(false))
        {
            results.Add(result);
        }

        return results.ToArray();
    }

    /// <summary>
    /// Filters the elements of an async-enumerable sequence based on a predicate.
    /// </summary>
    /// <typeparam name="TSource">The type of the elements in the source sequence.</typeparam>
    /// <param name="source">An async-enumerable sequence whose elements to filter.</param>
    /// <param name="predicate">A function to test each source element for a condition.</param>
    /// <returns>An async-enumerable sequence that contains elements from the input sequence that satisfy the condition.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="source"/> or <paramref name="predicate"/> is null.</exception>
    public static async IAsyncEnumerable<TSource> Where<TSource>(this IAsyncEnumerable<TSource> source, Func<TSource, bool> predicate)
    {
        await foreach (var result in source.ConfigureAwait(false))
        {
            if (predicate(result))
            {
                yield return result;
            }
        }
    }

    private sealed class EmptyAsyncEnumerable<T> : IAsyncEnumerable<T>, IAsyncEnumerator<T>
    {
        public static readonly EmptyAsyncEnumerable<T> Instance = new();
        public IAsyncEnumerator<T> GetAsyncEnumerator(CancellationToken cancellationToken = default) => this;
        public ValueTask<bool> MoveNextAsync() => new(false);
        public T Current => default!;
        public ValueTask DisposeAsync() => default;
    }
}
