// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresVectorStoreUtils
{
    /// <summary>
    /// Wraps an <see cref="IAsyncEnumerable{T}"/> in an <see cref="IAsyncEnumerable{T}"/> that will throw a <see cref="VectorStoreOperationException"/>
    /// if an exception is thrown while iterating over the original enumerator.
    /// </summary>
    /// <typeparam name="T">The type of the items in the async enumerable.</typeparam>
    /// <param name="asyncEnumerable">The async enumerable to wrap.</param>
    /// <param name="operationName">The name of the operation being performed.</param>
    /// <param name="vectorStoreName">The name of the vector store.</param>
    /// <param name="collectionName">The name of the collection being operated on.</param>
    /// <returns>An async enumerable that will throw a <see cref="VectorStoreOperationException"/> if an exception is thrown while iterating over the original enumerator.</returns>
    public static async IAsyncEnumerable<T> WrapAsyncEnumerableAsync<T>(
        IAsyncEnumerable<T> asyncEnumerable,
        string operationName,
        string? vectorStoreName = null,
        string? collectionName = null)
    {
        var enumerator = asyncEnumerable.ConfigureAwait(false).GetAsyncEnumerator();

        var nextResult = await GetNextAsync<T>(enumerator, operationName, vectorStoreName, collectionName).ConfigureAwait(false);
        while (nextResult.more)
        {
            yield return nextResult.item;
            nextResult = await GetNextAsync(enumerator, operationName, vectorStoreName, collectionName).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Helper method to get the next index name from the enumerator with a try catch around the move next call to convert
    /// exceptions to <see cref="VectorStoreOperationException"/>.
    /// </summary>
    /// <param name="enumerator">The enumerator to get the next result from.</param>
    /// <param name="operationName">The name of the operation being performed.</param>
    /// <param name="vectorStoreName">The name of the vector store.</param>
    /// <param name="collectionName">The name of the collection being operated on.</param>
    /// <returns>A value indicating whether there are more results and the current string if true.</returns>
    public static async Task<(T item, bool more)> GetNextAsync<T>(
        ConfiguredCancelableAsyncEnumerable<T>.Enumerator enumerator,
        string operationName,
        string? vectorStoreName = null,
        string? collectionName = null)
    {
        try
        {
            var more = await enumerator.MoveNextAsync();
            return (enumerator.Current, more);
        }
        catch (Exception ex) when (ex is not (NotSupportedException or ArgumentException))
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = PostgresConstants.VectorStoreSystemName,
                VectorStoreName = vectorStoreName,
                CollectionName = collectionName,
                OperationName = operationName
            };
        }
    }
}
