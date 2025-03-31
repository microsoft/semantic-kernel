// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Xunit;

namespace VectorData.UnitTests;

public abstract class BaseLoggingTests
{
    protected static void AssertLog(
        List<(LogLevel Level, string Message, Exception? Exception)> logs,
        LogLevel logLevel,
        string message,
        Exception? exception = null)
    {
        Assert.Contains(logs, log => log.Level == logLevel && log.Message.Contains(message) && log.Exception == exception);
    }

    protected static async Task<Exception> AssertThrowsAsync<TException, TResult>(Func<ValueTask<TResult>> operation)
    {
        Exception? exception = null;

        try
        {
            await operation();
        }
#pragma warning disable CA1031 // Do not catch general exception types
        catch (Exception ex)
#pragma warning restore CA1031 // Do not catch general exception types
        {
            exception = ex;
        }

        Assert.NotNull(exception);
        Assert.IsType<TException>(exception);

        return exception;
    }
}
