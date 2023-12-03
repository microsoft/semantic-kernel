// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text;
using Microsoft.Extensions.Logging;
using Xunit.Abstractions;

namespace SemanticKernel.Experimental.Agents.Tests;

/// <summary>
/// A logger that writes to the Xunit test output
/// </summary>
internal class XunitLoggerProvider : ILoggerProvider
{
    private readonly ITestOutputHelper _output;
    private readonly LogLevel _minLevel;
    private readonly DateTimeOffset? _logStart;

    public XunitLoggerProvider(ITestOutputHelper output)
        : this(output, LogLevel.Trace)
    {
    }

    public XunitLoggerProvider(ITestOutputHelper output, LogLevel minLevel)
        : this(output, minLevel, null)
    {
    }

    public XunitLoggerProvider(ITestOutputHelper output, LogLevel minLevel, DateTimeOffset? logStart)
    {
        _output = output;
        _minLevel = minLevel;
        _logStart = logStart;
    }

    public ILogger CreateLogger(string categoryName)
    {
        return new XunitLogger(_output, categoryName, _minLevel, _logStart);
    }

    public void Dispose()
    {
    }
}

internal class XunitLogger : ILogger
{
    private static readonly string[] s_newLineChars = new[] { Environment.NewLine };
    private readonly string _category;
    private readonly LogLevel _minLogLevel;
    private readonly ITestOutputHelper _output;
    private DateTimeOffset? _logStart;

    public XunitLogger(ITestOutputHelper output, string category, LogLevel minLogLevel, DateTimeOffset? logStart)
    {
        _minLogLevel = minLogLevel;
        _category = category;
        _output = output;
        _logStart = logStart;
    }

    public void Log<TState>(
        LogLevel logLevel, EventId eventId, TState state, Exception exception, Func<TState, Exception, string> formatter)
    {
        try
        {
            _output.WriteLine(formatter(state, exception));
        }
        catch (Exception)
        {
            // We could fail because we're on a background thread and our captured ITestOutputHelper is
            // busted (if the test "completed" before the background thread fired).
            // So, ignore this. There isn't really anything we can do but hope the
            // caller has additional loggers registered
        }
    }

    public bool IsEnabled(LogLevel logLevel)
        => logLevel >= _minLogLevel;

    public IDisposable BeginScope<TState>(TState state)
        => new NullScope();

    private class NullScope : IDisposable
    {
        public void Dispose()
        {
        }
    }
}
