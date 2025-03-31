// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

/// <summary>
/// A logger that writes to the Xunit test output
/// </summary>
internal sealed class XunitLogger(ITestOutputHelper output, LogLevel? logLevel = null) : ILoggerFactory, ILogger, IDisposable
{
    private readonly LogLevel? _logLevel = logLevel;

    private object? _scopeState;

    /// <inheritdoc/>
    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        var localState = state?.ToString();
        var line = this._scopeState is not null ? $"{this._scopeState} {localState}" : localState;
        output.WriteLine(line);
    }

    /// <inheritdoc/>
    public bool IsEnabled(LogLevel logLevel) => this._logLevel == null || this._logLevel <= logLevel;

    /// <inheritdoc/>
    public IDisposable BeginScope<TState>(TState state) where TState : notnull
    {
        this._scopeState = state;
        return this;
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        // This class is marked as disposable to support the BeginScope method.
        // However, there is no need to dispose anything.
    }

    public ILogger CreateLogger(string categoryName) => this;

    public void AddProvider(ILoggerProvider provider) => throw new NotSupportedException();
}
