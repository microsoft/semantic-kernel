// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Skills.Memory.Qdrant.SDKClient.Internal.Diagnostics;

public static class LoggerExtensions
{
    public static void Trace(this ILogger logger, string? message = null, params object[] args)
    {
        logger.LogTrace(message, args);
    }

    public static void Trace(this ILogger logger, Exception? exception = null, string? message = null, params object[] args)
    {
        logger.LogTrace(exception, message, args);
    }

    public static void Debug(this ILogger logger, string? message = null, params object[] args)
    {
        logger.LogDebug(message, args);
    }

    public static void Debug(this ILogger logger, Exception? exception = null, string? message = null, params object[] args)
    {
        logger.LogDebug(exception, message, args);
    }

    public static void Info(this ILogger logger, string? message = null, params object[] args)
    {
        logger.LogInformation(message, args);
    }

    public static void Info(this ILogger logger, Exception exception, string? message = null, params object[] args)
    {
        logger.LogInformation(exception, message, args);
    }

    public static void Warn(this ILogger logger, string? message = null, params object[] args)
    {
        logger.LogWarning(message, args);
    }

    public static void Warn(this ILogger logger, Exception exception, string? message = null, params object[] args)
    {
        logger.LogWarning(exception, message, args);
    }

    public static void Error(this ILogger logger, string? message = null, params object[] args)
    {
        logger.LogError(message, args);
    }

    public static void Error(this ILogger logger, Exception exception, string? message = null, params object[] args)
    {
        logger.LogError(exception, message, args);
    }

    public static void Critical(this ILogger logger, string? message = null, params object[] args)
    {
        logger.LogCritical(message, args);
    }

    public static void Critical(this ILogger logger, Exception exception, string? message = null, params object[] args)
    {
        logger.LogCritical(exception, message, args);
    }

    public static ILogger DefaultIfNull(this ILogger? logger)
    {
        return logger != null ? logger : ConsoleLogger.Log;
    }

    public static ILogger<TLogger> DefaultIfNull<TLogger>(this ILogger<TLogger>? logger)
    {
        return logger != null ? logger : ConsoleLogger<TLogger>.Log;
    }

    public static ILoggerFactory DefaultIfNull(this ILoggerFactory? factory)
    {
        return factory != null ? factory : ConsoleLogger.Factory;
    }
}
