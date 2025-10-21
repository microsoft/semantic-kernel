// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.Extensions.Logging;

public static class Tools
{
    // logs a warning message indicating that an operation (such as playback) was interrupted by user voice.
    public static void LogInterrupted(this ILogger logger) => logger.LogWarning("Operation is cancelled by user interrupt.");

    // Executes a pipeline operation with latency logging and error handling
    public static async Task<T> ExecutePipelineOperationAsync<T>(
        Func<Task<T>> operation,
        string operationName,
        ILogger logger,
        CancellationToken cancellationToken = default,
        T? defaultValue = default,
        Func<T, string>? resultFormatter = null)
    {
        var timer = Stopwatch.StartNew();
        logger.LogInformation("{OperationName} starting...", operationName);

        try
        {
            var result = await operation().ConfigureAwait(false);
            timer.Stop();

            var resultInfo = resultFormatter?.Invoke(result) ?? result?.ToString() ?? "";
            if (string.IsNullOrEmpty(resultInfo))
            {
                logger.LogInformation("{OperationName} completed in {Duration:F4}sec", operationName, timer.Elapsed.TotalSeconds);
            }
            else
            {
                logger.LogInformation("{OperationName} completed in {Duration:F4}sec: {Result}", operationName, timer.Elapsed.TotalSeconds, resultInfo);
            }

            return result;
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            logger.LogInterrupted();
            return defaultValue!;
        }
        catch (TaskCanceledException) when (cancellationToken.IsCancellationRequested)
        {
            logger.LogInterrupted();
            return defaultValue!;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error during {OperationName}", operationName);
            return defaultValue!;
        }
    }

    public static async Task ExecutePipelineOperationAsync(
        Func<Task> operation,
        string operationName,
        ILogger logger,
        CancellationToken cancellationToken = default)
    {
        await ExecutePipelineOperationAsync<object?>(
            async () =>
            {
                await operation().ConfigureAwait(false);
                return null; // Return null for void operations
            },
            operationName,
            logger,
            cancellationToken,
            defaultValue: null
        ).ConfigureAwait(false);
    }
}
