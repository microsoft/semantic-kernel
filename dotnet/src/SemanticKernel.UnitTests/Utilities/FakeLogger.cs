// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace SemanticKernel.UnitTests.Utilities;

public class FakeLogger : ILogger
{
    public List<(LogLevel Level, string Message, Exception? Exception)> Logs { get; } = new();

    public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;

    public bool IsEnabled(LogLevel logLevel) => true;

    public void Log<TState>(
        LogLevel logLevel,
        EventId eventId,
        TState state,
        Exception? exception,
        Func<TState, Exception?, string> formatter)
    {
        var message = formatter(state, exception);
        this.Logs.Add((logLevel, message, exception));
    }
}
