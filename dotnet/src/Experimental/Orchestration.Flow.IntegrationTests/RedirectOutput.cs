// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Orchestration.Flow.IntegrationTests;

public sealed class RedirectOutput : TextWriter, ILogger, ILoggerFactory
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

    IDisposable ILogger.BeginScope<TState>(TState state)
    {
        return null!;
    }

    bool ILogger.IsEnabled(LogLevel logLevel)
    {
        return true;
    }

    public string GetLogs()
    {
        return this._logs.ToString();
    }

    void ILogger.Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter)
    {
        var message = formatter(state, exception);
        this._output?.WriteLine(message);
        this._logs.AppendLine(message);
    }

    ILogger ILoggerFactory.CreateLogger(string categoryName) => this;

    void ILoggerFactory.AddProvider(ILoggerProvider provider) => throw new NotSupportedException();
}
