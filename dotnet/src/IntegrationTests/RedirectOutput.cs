// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests;

public class RedirectOutput(ITestOutputHelper output) : TextWriter, ILogger, ILoggerFactory
{
    private readonly ITestOutputHelper _output = output;
    private readonly StringBuilder _logs = new();

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
        try
        {
            var message = formatter(state, exception);
            this._logs.AppendLine(message);
            this._output?.WriteLine(message);
        }
        catch (InvalidOperationException ioe)
        {
            Console.WriteLine($"RedirectOutput failed, reason: {ioe}");
        }
    }

    public ILogger CreateLogger(string categoryName) => this;

    public void AddProvider(ILoggerProvider provider) => throw new NotSupportedException();
}
