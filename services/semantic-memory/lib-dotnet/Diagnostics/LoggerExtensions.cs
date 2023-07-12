// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Services.Diagnostics;

public static class LoggerExtensions
{
    public static string GetLogLevelName(this ILogger log)
    {
        if (log.IsEnabled(LogLevel.Trace))
        {
            return "Trace";
        }

        if (log.IsEnabled(LogLevel.Debug))
        {
            return "Debug";
        }

        if (log.IsEnabled(LogLevel.Information))
        {
            return "Information";
        }

        if (log.IsEnabled(LogLevel.Warning))
        {
            return "Warning";
        }

        if (log.IsEnabled(LogLevel.Error))
        {
            return "Error";
        }

        if (log.IsEnabled(LogLevel.Critical))
        {
            return "Critical";
        }

        return "None";
    }
}
