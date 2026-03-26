// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Concurrent;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Npgsql;
using static Microsoft.Extensions.VectorData.VectorStoreErrorHandler;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal static class PostgresUtils
{
    private static readonly ConcurrentDictionary<Type, MethodInfo?> s_reloadTypesAsyncWithTokenMethods = new();

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

    /// <summary>
    /// Reloads PostgreSQL type mappings in a way that remains compatible across Npgsql major versions.
    /// </summary>
    /// <remarks>
    /// Npgsql 8 exposes <c>ReloadTypesAsync()</c>, while newer versions expose <c>ReloadTypesAsync(CancellationToken)</c>.
    /// SK currently compiles against Npgsql 8, so direct calls to one signature may fail at runtime when another version is loaded.
    /// </remarks>
    internal static Task ReloadTypesAsyncCompat(object connection, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(connection);

        MethodInfo? reloadTypesWithToken = GetReloadTypesAsyncMethod(connection.GetType());
        if (reloadTypesWithToken is null)
        {
            throw new MissingMethodException("No compatible ReloadTypesAsync overload found.");
        }

        object?[] parameters = reloadTypesWithToken.GetParameters().Length == 0 ? [] : [cancellationToken];
        return (Task)reloadTypesWithToken.Invoke(connection, parameters)!;
    }

    private static MethodInfo? GetReloadTypesAsyncMethod(Type connectionType)
        => s_reloadTypesAsyncWithTokenMethods.GetOrAdd(connectionType, static type => CreateReloadTypesAsyncMethod(type));

    [UnconditionalSuppressMessage("Trimming", "IL2070", Justification = "Best-effort runtime compatibility probe for optional API shape.")]
    private static MethodInfo? CreateReloadTypesAsyncMethod(Type connectionType)
    {
        MethodInfo? method = connectionType.GetMethod("ReloadTypesAsync", [typeof(CancellationToken)]);
        if (method is not null && method.ReturnType == typeof(Task))
        {
            return method;
        }

        method = connectionType.GetMethod("ReloadTypesAsync", Type.EmptyTypes);
        return method is not null && method.ReturnType == typeof(Task) ? method : null;
    }
}
