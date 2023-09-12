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
    // ReSharper disable once InconsistentNaming
    public static async Task Main(string[] args)
    {
        // Load configuration from environment variables or user secrets.
        LoadUserSecrets();

        // Execution canceled if the user presses Ctrl+C.
        using CancellationTokenSource cancellationTokenSource = new();
        CancellationToken cancelToken = cancellationTokenSource.ConsoleCancellationToken();

        string? defaultFilter = null; // Modify to filter examples

        // Check if args[0] is provided
        string? filter = args.Length > 0 ? args[0] : defaultFilter;

        // Run examples based on the filter
        await RunExamplesAsync(filter, cancelToken);
    }

    private static async Task RunExamplesAsync(string? filter, CancellationToken cancellationToken)
    {
        var examples = (Assembly.GetExecutingAssembly().GetTypes())
            .Where(type => type.Name.StartsWith("Example", StringComparison.OrdinalIgnoreCase))
            .Select(type => type.Name).ToList();

        // Filter and run examples
        foreach (var example in examples)
        {
            if (string.IsNullOrEmpty(filter) || example.Contains(filter, StringComparison.OrdinalIgnoreCase))
            {
                try
                {
                    Console.WriteLine($"Running {example}...");

                    var method = Assembly.GetExecutingAssembly().GetType(example)?.GetMethod("RunAsync");
                    if (method == null)
                    {
                        Console.WriteLine($"Example {example} not found");
                        continue;
                    }

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


    private static async Task SafeWaitAsync(
        this Task task,
        CancellationToken cancellationToken = default)
    {
        try
        {
            await task.WaitAsync(cancellationToken);
            Console.WriteLine("== DONE ==");
        }
        catch (ConfigurationNotFoundException ex)
        {
            Console.WriteLine($"{ex.Message}. Skipping example.");
        }

        cancellationToken.ThrowIfCancellationRequested();
    }
}
