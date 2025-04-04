// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Diagnostics;

[ExcludeFromCodeCoverage]
internal static partial class LoggingExtensions
{
    internal static async Task RunWithLoggingAsync(
        ILogger logger,
        string operationName,
        Func<Task> operation)
    {
        logger.LogInvoked(operationName);

        try
        {
            await operation().ConfigureAwait(false);

            logger.LogCompleted(operationName);
        }
        catch (OperationCanceledException)
        {
            logger.LogInvocationCanceled(operationName);
            throw;
        }
        catch (Exception ex)
        {
            logger.LogInvocationFailed(operationName, ex);
            throw;
        }
    }

    internal static async Task<TResult> RunWithLoggingAsync<TResult>(
        ILogger logger,
        string operationName,
        Func<Task<TResult>> operation)
    {
        logger.LogInvoked(operationName);

        try
        {
            var result = await operation().ConfigureAwait(false);

            logger.LogCompleted(operationName);

            return result;
        }
        catch (OperationCanceledException)
        {
            logger.LogInvocationCanceled(operationName);
            throw;
        }
        catch (Exception ex)
        {
            logger.LogInvocationFailed(operationName, ex);
            throw;
        }
    }

    internal static async IAsyncEnumerable<TResult> RunWithLoggingAsync<TResult>(
        ILogger logger,
        string operationName,
        Func<IAsyncEnumerable<TResult>> operation,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        logger.LogInvoked(operationName);

        IAsyncEnumerator<TResult> enumerator;

        try
        {
            enumerator = operation().GetAsyncEnumerator(cancellationToken);
        }
        catch (OperationCanceledException)
        {
            logger.LogInvocationCanceled(operationName);
            throw;
        }
        catch (Exception ex)
        {
            logger.LogInvocationFailed(operationName, ex);
            throw;
        }

        try
        {
            while (true)
            {
                try
                {
                    if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                    {
                        break;
                    }
                }
                catch (OperationCanceledException)
                {
                    logger.LogInvocationCanceled(operationName);
                    throw;
                }
                catch (Exception ex)
                {
                    logger.LogInvocationFailed(operationName, ex);
                    throw;
                }

                yield return enumerator.Current;
            }

            logger.LogCompleted(operationName);
        }
        finally
        {
            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    [LoggerMessage(LogLevel.Debug, "{OperationName} invoked.")]
    private static partial void LogInvoked(this ILogger logger, string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} completed.")]
    private static partial void LogCompleted(this ILogger logger, string operationName);

    [LoggerMessage(LogLevel.Debug, "{OperationName} canceled.")]
    private static partial void LogInvocationCanceled(this ILogger logger, string operationName);

    [LoggerMessage(LogLevel.Error, "{OperationName} failed.")]
    private static partial void LogInvocationFailed(this ILogger logger, string operationName, Exception exception);
}
