// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
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
    /// <summary>
    /// Run the given model conversion and wrap any exceptions with <see cref="VectorStoreRecordMappingException"/>.
    /// </summary>
    /// <typeparam name="T">The response type of the operation.</typeparam>
    /// <param name="vectorStoreSystemName">The name of the vector store system the operation is being run on.</param>
    /// <param name="vectorStoreName">The name of the vector store the operation is being run on.</param>
    /// <param name="collectionName">The name of the collection the operation is being run on.</param>
    /// <param name="operationName">The type of database operation being run.</param>
    /// <param name="operation">The operation to run.</param>
    /// <returns>The result of the operation.</returns>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    public static T RunModelConversion<T>(
        string vectorStoreSystemName,
        string? vectorStoreName,
        string collectionName,
        string operationName,
        Func<T> operation)
    {
        try
        {
            return operation.Invoke();
        }
        catch (Exception ex)
        {
            throw new VectorStoreRecordMappingException("Failed to convert vector store record.", ex)
            {
                VectorStoreSystemName = vectorStoreSystemName,
                VectorStoreName = vectorStoreName,
                CollectionName = collectionName,
                OperationName = operationName
            };
        }
    }

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
}
