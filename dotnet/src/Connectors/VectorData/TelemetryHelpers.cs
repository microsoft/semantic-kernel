// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Class with helper methods to run operations with telemetry.
/// </summary>
internal static class TelemetryHelpers
{
    /// <summary>
    /// Method to run operation which doesn't return a result.
    /// </summary>
    internal static async Task RunOperationAsync(
        ActivitySource activitySource,
        string operationName,
        string? collectionName,
        string? databaseName,
        string? vectorStoreSystemName,
        Histogram<double> operationDurationHistogram,
        Func<Task> operation)
    {
        using var activity = activitySource.StartActivity(operationName, collectionName, databaseName, vectorStoreSystemName);
        Stopwatch? stopwatch = operationDurationHistogram.Enabled ? Stopwatch.StartNew() : null;

        Exception? exception = null;

        try
        {
            await operation().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            exception = ex;
            throw;
        }
        finally
        {
            TelemetryHelpers.TraceOperationCompletion(
                operationName,
                collectionName,
                databaseName,
                vectorStoreSystemName,
                operationDurationHistogram,
                activity,
                exception,
                stopwatch);
        }
    }

    /// <summary>
    /// Method to run operation which returns the result.
    /// </summary>
    internal static async Task<TResult> RunOperationAsync<TResult>(
        ActivitySource activitySource,
        string operationName,
        string? collectionName,
        string? databaseName,
        string? vectorStoreSystemName,
        Histogram<double> operationDurationHistogram,
        Func<Task<TResult>> operation)
    {
        using var activity = activitySource.StartActivity(operationName, collectionName, databaseName, vectorStoreSystemName);
        Stopwatch? stopwatch = operationDurationHistogram.Enabled ? Stopwatch.StartNew() : null;

        Exception? exception = null;

        try
        {
            return await operation().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            exception = ex;
            throw;
        }
        finally
        {
            TelemetryHelpers.TraceOperationCompletion(
            operationName,
                collectionName,
                databaseName,
                vectorStoreSystemName,
                operationDurationHistogram,
                activity,
                exception,
                stopwatch);
        }
    }

    /// <summary>
    /// Method to run operation which returns async enumeration.
    /// </summary>
    internal static async IAsyncEnumerable<TResult> RunOperationAsync<TResult>(
        ActivitySource activitySource,
        string operationName,
        string? collectionName,
        string? databaseName,
        string? vectorStoreSystemName,
        Histogram<double> operationDurationHistogram,
        Func<IAsyncEnumerable<TResult>> operation,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using var activity = activitySource.StartActivity(operationName, collectionName, databaseName, vectorStoreSystemName);
        Stopwatch? stopwatch = operationDurationHistogram.Enabled ? Stopwatch.StartNew() : null;

        IAsyncEnumerator<TResult> enumerator;

        try
        {
            enumerator = operation().GetAsyncEnumerator(cancellationToken);
        }
        catch (Exception ex)
        {
            TelemetryHelpers.TraceOperationCompletion(
                operationName,
                collectionName,
                databaseName,
                vectorStoreSystemName,
                operationDurationHistogram,
                activity,
                ex,
                stopwatch);

            throw;
        }

        Exception? exception = null;

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
                catch (Exception ex)
                {
                    exception = ex;
                    throw;
                }

                yield return enumerator.Current;
                Activity.Current = activity; // workaround for https://github.com/dotnet/runtime/issues/47802
            }
        }
        finally
        {
            TelemetryHelpers.TraceOperationCompletion(
                operationName,
                collectionName,
                databaseName,
                vectorStoreSystemName,
                operationDurationHistogram,
                activity,
                exception,
                stopwatch);

            await enumerator.DisposeAsync().ConfigureAwait(false);
        }
    }

    #region private

    private static Activity? StartActivity(
        this ActivitySource activitySource,
        string operationName,
        string? collectionName,
        string? databaseName,
        string? vectorStoreSystemName)
    {
        Activity? activity = null;

        if (activitySource.HasListeners())
        {
            activity = activitySource.StartActivity(
                OpenTelemetryConstants.GetActivityName(operationName, collectionName, databaseName),
                ActivityKind.Client);

            var tags = GetTags(operationName, collectionName, databaseName, vectorStoreSystemName);

            foreach (var tag in tags)
            {
                activity?.SetTag(tag.Key, tag.Value);
            }
        }

        return activity;
    }

    private static void TraceOperationCompletion(
        string operationName,
        string? collectionName,
        string? databaseName,
        string? vectorStoreSystemName,
        Histogram<double> operationDurationHistogram,
        Activity? activity,
        Exception? exception,
        Stopwatch? stopwatch)
    {
        if (operationDurationHistogram.Enabled && stopwatch is not null)
        {
            var tags = TelemetryHelpers.GetTags(operationName, collectionName, databaseName, vectorStoreSystemName);

            if (exception is not null)
            {
                tags.Add(OpenTelemetryConstants.ErrorType, exception.GetType().FullName);
            }

            operationDurationHistogram.Record(stopwatch.Elapsed.TotalSeconds, tags);
        }

        if (exception is not null)
        {
            activity?
                .SetTag(OpenTelemetryConstants.ErrorType, exception.GetType().FullName)
                .SetStatus(ActivityStatusCode.Error, exception.Message);
        }
    }

    private static TagList GetTags(
        string operationName,
        string? collectionName,
        string? databaseName,
        string? vectorStoreSystemName)
    {
        TagList tags = default;

        tags.Add(OpenTelemetryConstants.DbOperationName, operationName);

        if (!string.IsNullOrWhiteSpace(collectionName))
        {
            tags.Add(OpenTelemetryConstants.DbCollectionName, collectionName);
        }

        if (!string.IsNullOrWhiteSpace(databaseName))
        {
            tags.Add(OpenTelemetryConstants.DbNamespace, databaseName);
        }

        if (!string.IsNullOrWhiteSpace(vectorStoreSystemName))
        {
            tags.Add(OpenTelemetryConstants.DbSystemName, vectorStoreSystemName);
        }

        return tags;
    }

    #endregion
}
