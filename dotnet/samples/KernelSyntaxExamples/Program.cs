// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Reliability;
using RepoUtils;

public static class Program
{
    /// <summary>
    /// We recommend using the Debug properties to set the filter as a command line argument.
    /// If you don't want to use it, set the filter here.
    /// Examples:
    ///     DefaultFilter = "18"    => run only example 18 (also "180" if there is such test)
    ///     DefaultFilter = "chat"  => run all examples with a name that contains "chat"
    /// </summary>
    public const string? DefaultFilter = "";

    public static async Task Main(string[] args)
    {
        // Load configuration from environment variables or user secrets.
        LoadUserSecrets();

        // Execution canceled if the user presses Ctrl+C.
        using CancellationTokenSource cancellationTokenSource = new();
        CancellationToken cancelToken = cancellationTokenSource.ConsoleCancellationToken();

        // Check if args[0] is provided
        string? filter = args.Length > 0 ? args[0] : DefaultFilter;

        // Run examples based on the filter
        await RunExamplesAsync(filter, cancelToken);
    }

    private static async Task RunExamplesAsync(string? filter, CancellationToken cancellationToken)
    {
        var examples = (Assembly.GetExecutingAssembly().GetTypes())
            .Select(type => type.Name).ToList();

        // Filter and run examples
        foreach (var example in examples)
        {
            if (string.IsNullOrEmpty(filter) || example.Contains(filter, StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    var method = Assembly.GetExecutingAssembly().GetType(example)?.GetMethod("RunAsync");
                    if (method == null)
                    {
                        // Skip if the type does not have a RunAsync method
                        continue;
                    }

                    Console.WriteLine($"Running {example}...");

                    bool hasCancellationToken = method.GetParameters().Any(param => param.ParameterType == typeof(CancellationToken));

                    var taskParameters = hasCancellationToken ? new object[] { cancellationToken } : null;
                    if (method.Invoke(null, taskParameters) is Task t)
                    {
                        await t.SafeWaitAsync(cancellationToken);
                    }
                    else
                    {
                        method.Invoke(null, null);
                    }
                }
                catch (ConfigurationNotFoundException ex)
                {
                    Console.WriteLine($"{ex.Message}. Skipping example {example}.");
                }
            }
        }
    }

    private static void LoadUserSecrets()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddJsonFile("appsettings.Development.json", true)
            .AddEnvironmentVariables()
            .AddUserSecrets<Env>()
            .Build();
        TestConfiguration.Initialize(configRoot);
    }

    private static CancellationToken ConsoleCancellationToken(this CancellationTokenSource tokenSource)
    {
        Console.CancelKeyPress += (s, e) =>
        {
            Console.WriteLine("Canceling...");
            tokenSource.Cancel();
            e.Cancel = true;
        };

        return tokenSource.Token;
    }

    private static async Task SafeWaitAsync(this Task task,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await task.WaitAsync(cancellationToken);
            Console.WriteLine();
            Console.WriteLine("== DONE ==");
        }
        catch (ConfigurationNotFoundException ex)
        {
            Console.WriteLine($"{ex.Message}. Skipping example.");
        }

        cancellationToken.ThrowIfCancellationRequested();
    }
}
