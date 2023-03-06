// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Console;

namespace Qdrant.DotNet.Internal.Diagnostics;

public static class ConsoleLogger
{
    private const string DEFAULT_CATEGORYNAME = "LOG";

    public static ILogger Log
    {
        get { return Create(DEFAULT_CATEGORYNAME); }
    }

    public static ILogger Create(string categoryName)
    {
        return Factory.CreateLogger(categoryName);
    }

    public static ILogger Create(string categoryName, Action<SimpleConsoleFormatterOptions> options)
    {
        return LoggerFactory.Create(builder =>
            builder.AddSimpleConsole(options)).CreateLogger(categoryName);
    }

    private static ILoggerFactory? s_loggerFactory = null;

    public static ILoggerFactory Factory
    {
        get
        {
            s_loggerFactory = s_loggerFactory ?? LoggerFactory.Create(builder =>
                builder.AddSimpleConsole(options =>
                {
                    options.IncludeScopes = true;
                }));

            return s_loggerFactory;
        }
    }
}

public static class ConsoleLogger<T>
{
    public static ILogger<T> Log
    {
        get { return Create(); }
    }

    public static ILogger<T> Create()
    {
        return ConsoleLogger.Factory.CreateLogger<T>();
    }

    public static ILogger<T> Create(Action<SimpleConsoleFormatterOptions> options)
    {
        return LoggerFactory.Create(builder =>
            builder.AddSimpleConsole(options)).CreateLogger<T>();
    }
}
