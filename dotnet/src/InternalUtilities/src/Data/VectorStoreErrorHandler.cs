// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

#pragma warning disable MEVD9000 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.

/// <summary>
/// Contains helpers for reading vector store model properties and their attributes.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class VectorStoreErrorHandler
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static Task<TResult> RunOperationAsync<TResult, TException>(
        VectorStoreMetadata metadata,
        string operationName,
        Func<Task<TResult>> operation)
        where TException : Exception
    {
        return RunOperationAsync<TResult, TException>(
            new VectorStoreRecordCollectionMetadata()
            {
                CollectionName = null,
                VectorStoreName = metadata.VectorStoreName,
                VectorStoreSystemName = metadata.VectorStoreSystemName,
            },
            operationName,
            operation);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static async Task<TResult> RunOperationAsync<TResult, TException>(
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        Func<Task<TResult>> operation)
        where TException : Exception
    {
        try
        {
            return await operation.Invoke().ConfigureAwait(false);
        }
        catch (AggregateException ex) when (ex.InnerException is TException innerEx)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
        catch (TException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static TResult RunOperation<TResult, TException>(
        VectorStoreMetadata metadata,
        string operationName,
        Func<TResult> operation)
        where TException : Exception
    {
        return RunOperation<TResult, TException>(
            new VectorStoreRecordCollectionMetadata()
            {
                CollectionName = null,
                VectorStoreName = metadata.VectorStoreName,
                VectorStoreSystemName = metadata.VectorStoreSystemName,
            },
            operationName,
            operation);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static TResult RunOperation<TResult, TException>(
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        Func<TResult> operation)
        where TException : Exception
    {
        try
        {
            return operation.Invoke();
        }
        catch (AggregateException ex) when (ex.InnerException is TException innerEx)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
        catch (TException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static async Task<TResult> RunOperationWithRetryAsync<TResult, TException>(
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        int maxRetries,
        int delayInMilliseconds,
        Func<Task<TResult>> operation,
        CancellationToken cancellationToken)
        where TException : Exception
    {
        var retries = 0;

        var exceptions = new List<Exception>();

        while (retries < maxRetries)
        {
            try
            {
                return await operation.Invoke().ConfigureAwait(false);
            }
            catch (AggregateException ex) when (ex.InnerException is TException innerEx)
            {
                retries++;
                exceptions.Add(ex);

                if (retries >= maxRetries)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", new AggregateException(exceptions))
                    {
                        VectorStoreSystemName = metadata.VectorStoreSystemName,
                        VectorStoreName = metadata.VectorStoreName,
                        CollectionName = metadata.CollectionName,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
            catch (TException ex)
            {
                retries++;
                exceptions.Add(ex);

                if (retries >= maxRetries)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", new AggregateException(exceptions))
                    {
                        VectorStoreSystemName = metadata.VectorStoreSystemName,
                        VectorStoreName = metadata.VectorStoreName,
                        CollectionName = metadata.CollectionName,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
        }

        throw new VectorStoreOperationException("Call to vector store failed.", new AggregateException(exceptions))
        {
            VectorStoreSystemName = metadata.VectorStoreSystemName,
            VectorStoreName = metadata.VectorStoreName,
            CollectionName = metadata.CollectionName,
            OperationName = operationName
        };
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static async Task RunOperationAsync<TException>(
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        Func<Task> operation)
        where TException : Exception
    {
        try
        {
            await operation.Invoke().ConfigureAwait(false);
        }
        catch (AggregateException ex) when (ex.InnerException is TException innerEx)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
        catch (TException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static async Task RunOperationWithRetryAsync<TException>(
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        int maxRetries,
        int delayInMilliseconds,
        Func<Task> operation,
        CancellationToken cancellationToken)
        where TException : Exception
    {
        var retries = 0;

        var exceptions = new List<Exception>();

        while (retries < maxRetries)
        {
            try
            {
                await operation.Invoke().ConfigureAwait(false);
                return;
            }
            catch (AggregateException ex) when (ex.InnerException is TException innerEx)
            {
                retries++;
                exceptions.Add(ex);

                if (retries >= maxRetries)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", new AggregateException(exceptions))
                    {
                        VectorStoreSystemName = metadata.VectorStoreSystemName,
                        VectorStoreName = metadata.VectorStoreName,
                        CollectionName = metadata.CollectionName,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
            catch (TException ex)
            {
                retries++;
                exceptions.Add(ex);

                if (retries >= maxRetries)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", new AggregateException(exceptions))
                    {
                        VectorStoreSystemName = metadata.VectorStoreSystemName,
                        VectorStoreName = metadata.VectorStoreName,
                        CollectionName = metadata.CollectionName,
                        OperationName = operationName
                    };
                }

                await Task.Delay(delayInMilliseconds, cancellationToken).ConfigureAwait(false);
            }
        }

        throw new VectorStoreOperationException("Call to vector store failed.", new AggregateException(exceptions))
        {
            VectorStoreSystemName = metadata.VectorStoreSystemName,
            VectorStoreName = metadata.VectorStoreName,
            CollectionName = metadata.CollectionName,
            OperationName = operationName
        };
    }

    public struct ConfiguredCancelableErrorHandlingAsyncEnumerable<TResult, TException>
        where TException : Exception
    {
        private readonly ConfiguredCancelableAsyncEnumerable<TResult> _enumerable;
        private readonly VectorStoreRecordCollectionMetadata _metadata;
        private readonly string _operationName;

        public ConfiguredCancelableErrorHandlingAsyncEnumerable(
            ConfiguredCancelableAsyncEnumerable<TResult> enumerable,
            VectorStoreRecordCollectionMetadata metadata,
            string operationName)
        {
            this._enumerable = enumerable;
            this._metadata = metadata;
            this._operationName = operationName;
        }

        public ConfiguredCancelableErrorHandlingAsyncEnumerable(
            ConfiguredCancelableAsyncEnumerable<TResult> enumerable,
            VectorStoreMetadata metadata,
            string operationName)
        {
            this._enumerable = enumerable;
            this._metadata = new()
            {
                CollectionName = null,
                VectorStoreName = metadata.VectorStoreName,
                VectorStoreSystemName = metadata.VectorStoreSystemName,
            };
            this._operationName = operationName;
        }

        public ConfiguredCancelableErrorHandlingAsyncEnumerable<TResult, TException>.Enumerator GetAsyncEnumerator(CancellationToken cancellationToken = default)
        {
            return new Enumerator(this._enumerable.WithCancellation(cancellationToken).GetAsyncEnumerator(), this._metadata, this._operationName);
        }

        public ConfiguredCancelableErrorHandlingAsyncEnumerable<TResult, TException> ConfigureAwait(bool continueOnCapturedContext)
        {
            return new ConfiguredCancelableErrorHandlingAsyncEnumerable<TResult, TException>(this._enumerable.ConfigureAwait(continueOnCapturedContext), this._metadata, this._operationName);
        }

        public struct Enumerator(
            ConfiguredCancelableAsyncEnumerable<TResult>.Enumerator enumerator,
            VectorStoreRecordCollectionMetadata metadata,
            string operationName)
        {
            public async ValueTask<bool> MoveNextAsync()
            {
                try
                {
                    return await enumerator.MoveNextAsync();
                }
                catch (AggregateException ex) when (ex.InnerException is TException innerEx)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", ex)
                    {
                        VectorStoreSystemName = metadata.VectorStoreSystemName,
                        VectorStoreName = metadata.VectorStoreName,
                        CollectionName = metadata.CollectionName,
                        OperationName = operationName
                    };
                }
                catch (TException ex)
                {
                    throw new VectorStoreOperationException("Call to vector store failed.", ex)
                    {
                        VectorStoreSystemName = metadata.VectorStoreSystemName,
                        VectorStoreName = metadata.VectorStoreName,
                        CollectionName = metadata.CollectionName,
                        OperationName = operationName
                    };
                }
            }
            public TResult Current => enumerator.Current;
        }
    }

    internal static Task<bool> ReadWithErrorHandlingAsync(
        this DbDataReader reader,
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        CancellationToken cancellationToken)
        => VectorStoreErrorHandler.RunOperationAsync<bool, DbException>(
            metadata,
            operationName,
            () => reader.ReadAsync(cancellationToken));

    internal static Task<bool> ReadWithErrorHandlingAsync(
        this DbDataReader reader,
        VectorStoreMetadata metadata,
        string operationName,
        CancellationToken cancellationToken)
        => VectorStoreErrorHandler.RunOperationAsync<bool, DbException>(
            metadata,
            operationName,
            () => reader.ReadAsync(cancellationToken));

    internal static async Task<TResult> ExecuteWithErrorHandlingAsync<TResult>(
        this DbConnection connection,
        VectorStoreMetadata metadata,
        string operationName,
        Func<Task<TResult>> operation,
        CancellationToken cancellationToken)
    {
        return await ExecuteWithErrorHandlingAsync(
            connection,
            new VectorStoreRecordCollectionMetadata
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = null
            },
            operationName,
            operation,
            cancellationToken).ConfigureAwait(false);
    }

    internal static async Task<TResult> ExecuteWithErrorHandlingAsync<TResult>(
        this DbConnection connection,
        VectorStoreRecordCollectionMetadata metadata,
        string operationName,
        Func<Task<TResult>> operation,
        CancellationToken cancellationToken)
    {
        if (connection.State != System.Data.ConnectionState.Open)
        {
            await connection.OpenAsync(cancellationToken).ConfigureAwait(false);
        }

        try
        {
            return await operation().ConfigureAwait(false);
        }
        catch (DbException ex)
        {
#if NET
            await connection.DisposeAsync().ConfigureAwait(false);
#else
            connection.Dispose();
#endif

            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
        catch (IOException ex)
        {
#if NET
            await connection.DisposeAsync().ConfigureAwait(false);
#else
            connection.Dispose();
#endif

            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = metadata.VectorStoreSystemName,
                VectorStoreName = metadata.VectorStoreName,
                CollectionName = metadata.CollectionName,
                OperationName = operationName
            };
        }
        catch (Exception)
        {
#if NET
            await connection.DisposeAsync().ConfigureAwait(false);
#else
            connection.Dispose();
#endif
            throw;
        }
    }
}
