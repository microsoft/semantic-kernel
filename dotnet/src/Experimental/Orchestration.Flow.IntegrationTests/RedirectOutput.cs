// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Text;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Orchestration.Flow.IntegrationTests;

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
public sealed class RedirectOutput(ITestOutputHelper output) : TextWriter, ILogger, ILoggerFactory
{
    private readonly ITestOutputHelper _output = output;
    private readonly StringBuilder _logs = new();
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
public sealed class RedirectOutput(ITestOutputHelper output) : TextWriter, ILogger, ILoggerFactory
{
    private readonly ITestOutputHelper _output = output;
    private readonly StringBuilder _logs = new();
=======
public sealed class RedirectOutput : TextWriter, ILogger, ILoggerFactory
{
    private readonly ITestOutputHelper _output;
    private readonly StringBuilder _logs;

    public RedirectOutput(ITestOutputHelper output)
    {
        this._output = output;
        this._logs = new StringBuilder();
    }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

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
