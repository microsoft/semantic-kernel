// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;
using static Microsoft.Extensions.VectorData.VectorStoreErrorHandler;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal static class PostgresUtils
{
    /// <summary>
    /// Wraps an <see cref="IAsyncEnumerable{T}"/> in an <see cref="IAsyncEnumerable{T}"/> that will throw a <see cref="VectorStoreException"/>
    /// if an exception is thrown while iterating over the original enumerator.
    /// </summary>
    /// <typeparam name="T">The type of the items in the async enumerable.</typeparam>
    /// <param name="asyncEnumerable">The async enumerable to wrap.</param>
    /// <param name="operationName">The name of the operation being performed.</param>
    /// <param name="metadata">The vector store metadata to describe the type of database.</param>
    /// <returns>An async enumerable that will throw a <see cref="VectorStoreException"/> if an exception is thrown while iterating over the original enumerator.</returns>
    public static async IAsyncEnumerable<T> WrapAsyncEnumerableAsync<T>(
        IAsyncEnumerable<T> asyncEnumerable,
        string operationName,
        VectorStoreMetadata metadata)
    {
        var errorHandlingEnumerable = new ConfiguredCancelableErrorHandlingAsyncEnumerable<T, NpgsqlException>(
            asyncEnumerable.ConfigureAwait(false),
            metadata,
            operationName);

#pragma warning disable CA2007 // Consider calling ConfigureAwait on the awaited task: False Positive
        await foreach (var item in errorHandlingEnumerable.ConfigureAwait(false))
#pragma warning restore CA2007 // Consider calling ConfigureAwait on the awaited task
        {
            yield return item;
        }
    }

    /// <summary>
    /// Wraps an <see cref="IAsyncEnumerable{T}"/> in an <see cref="IAsyncEnumerable{T}"/> that will throw a <see cref="VectorStoreException"/>
    /// if an exception is thrown while iterating over the original enumerator.
    /// </summary>
    /// <typeparam name="T">The type of the items in the async enumerable.</typeparam>
    /// <param name="asyncEnumerable">The async enumerable to wrap.</param>
    /// <param name="operationName">The name of the operation being performed.</param>
    /// <param name="metadata">The collection metadata to describe the type of database.</param>
    /// <returns>An async enumerable that will throw a <see cref="VectorStoreException"/> if an exception is thrown while iterating over the original enumerator.</returns>
    public static async IAsyncEnumerable<T> WrapAsyncEnumerableAsync<T>(
        IAsyncEnumerable<T> asyncEnumerable,
        string operationName,
        VectorStoreCollectionMetadata metadata)
    {
        var errorHandlingEnumerable = new ConfiguredCancelableErrorHandlingAsyncEnumerable<T, NpgsqlException>(
            asyncEnumerable.ConfigureAwait(false),
            metadata,
            operationName);

#pragma warning disable CA2007 // Consider calling ConfigureAwait on the awaited task: False Positive
        await foreach (var item in errorHandlingEnumerable.ConfigureAwait(false))
#pragma warning restore CA2007 // Consider calling ConfigureAwait on the awaited task
        {
            yield return item;
        }
    }

    internal static NpgsqlDataSource CreateDataSource(string connectionString)
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        NpgsqlDataSourceBuilder sourceBuilder = new(connectionString);
        sourceBuilder.UseVector();
        return sourceBuilder.Build();
    }
}
