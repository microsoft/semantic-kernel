// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
}
