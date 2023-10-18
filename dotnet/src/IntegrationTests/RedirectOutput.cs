// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests;

public class RedirectOutput : TextWriter, ILogger, ILoggerFactory
{
    private readonly ITestOutputHelper _output;
    private readonly StringBuilder _logs;

    public RedirectOutput(ITestOutputHelper output)
    {
        this._output = output;
        this._logs = new StringBuilder();
    }

    public override Encoding Encoding { get; } = Encoding.UTF8;

    public override void WriteLine(string? value)
    {
        this._output.WriteLine(value);
        this._logs.AppendLine(value);
    }

    public IDisposable BeginScope<TState>(TState state) where TState : notnull
    {
        return null!;
    }

    public bool IsEnabled(LogLevel logLevel)
    {
        return true;
    }

    public string GetLogs()
    {
        return this._logs.ToString();
    }

    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        var message = formatter(state, exception);
        this._output?.WriteLine(message);
        this._logs.AppendLine(message);
    }

    public ILogger CreateLogger(string categoryName) => this;

    public void AddProvider(ILoggerProvider provider) => throw new NotSupportedException();
}
