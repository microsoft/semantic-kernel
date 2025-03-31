// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;

namespace VectorData.UnitTests;

internal sealed class FakeLogger(LogLevel? logLevel = null) : ILogger
{
    private readonly LogLevel? _logLevel = logLevel;

    public List<(LogLevel Level, string Message, Exception? Exception)> Logs { get; } = new();

    public IDisposable? BeginScope<TState>(TState state) where TState : notnull => null;

    public bool IsEnabled(LogLevel logLevel) => this._logLevel == null || this._logLevel <= logLevel;

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
