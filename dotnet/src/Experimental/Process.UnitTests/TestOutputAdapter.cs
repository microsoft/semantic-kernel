// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests;

public sealed class TestOutputAdapter(ITestOutputHelper output) : TextWriter, ILogger, ILoggerFactory
{
    private readonly Stack<string> _scopes = [];

    public override Encoding Encoding { get; } = Encoding.UTF8;

    public void AddProvider(ILoggerProvider provider) => throw new NotSupportedException();

    public ILogger CreateLogger(string categoryName) => this;

    public bool IsEnabled(LogLevel logLevel) => true;

    public override void WriteLine(object? value = null) => this.SafeWrite($"{value}");

    public override void WriteLine(string? format, params object?[] arg) => this.SafeWrite(string.Format(format ?? string.Empty, arg));

    public override void WriteLine(string? value) => this.SafeWrite(value ?? string.Empty);

    public override void Write(object? value = null) => this.SafeWrite($"{value}");

    public override void Write(char[]? buffer) => this.SafeWrite(new string(buffer));

    public IDisposable BeginScope<TState>(TState state) where TState : notnull
    {
        this._scopes.Push($"{state}");
        return new LoggerScope(() => this._scopes.Pop());
    }

    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        string message = formatter(state, exception);
        string scope = this._scopes.Count > 0 ? $"[{this._scopes.Peek()}] " : string.Empty;
        output.WriteLine($"{scope}{message}");
    }

    private void SafeWrite(string value)
    {
        try
        {
            output.WriteLine(value ?? string.Empty);
        }
        catch (InvalidOperationException exception) when (exception.Message == "There is no currently active test.")
        {
            // This exception is thrown when the test output is accessed outside of a test context.
            // We can ignore it since we are not in a test context.
        }
    }

    private sealed class LoggerScope(Action action) : IDisposable
    {
        private bool _disposed;

        public void Dispose()
        {
            if (!this._disposed)
            {
                action.Invoke();
                this._disposed = true;
            }
        }
    }
}
