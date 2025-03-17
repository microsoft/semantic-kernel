// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using System.Collections.Generic;
using System;
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
}
