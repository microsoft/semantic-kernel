// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.ApplicationInsights;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.ApplicationInsights;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.Sequential;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public sealed class Example52_AppInsights
{
    private static LogLevel LogLevel = LogLevel.Trace;

    public static async Task RunAsync()
    {
        var serviceProvider = GetServiceProvider();
        var logger = serviceProvider.GetRequiredService<ILogger<Example52_AppInsights>>();
        var telemetryClient = serviceProvider.GetRequiredService<TelemetryClient>();

        var kernel = GetKernel(logger);
        var planner = GetPlanner(kernel, logger);

        using var operation = telemetryClient.StartOperation<DependencyTelemetry>("Planning");

        Console.WriteLine("Trace ID:");
        Console.WriteLine(Activity.Current?.TraceId);

        var plan = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");

        Console.WriteLine("Original plan:");
        Console.WriteLine(plan.ToPlanWithGoalString());

        var result = await kernel.RunAsync(plan);

        Console.WriteLine("Result:");
        Console.WriteLine(result.Result);

        // Explicitly call Flush() followed by sleep is required in console apps.
        // This is to ensure that even if application terminates, telemetry is sent to the back-end.
        telemetryClient.Flush();
        await Task.Delay(5000);
    }

    private static ServiceProvider GetServiceProvider()
    {
        var services = new ServiceCollection();

        ConfigureLogging(services);

        return services.BuildServiceProvider();
    }

    private static void ConfigureLogging(ServiceCollection services)
    {
        string instrumentationKey = Env.Var("APP_INSIGHTS_INSTRUMENTATION_KEY");

        services.AddLogging(loggingBuilder =>
        {
            loggingBuilder.AddFilter<ApplicationInsightsLoggerProvider>(typeof(Example52_AppInsights).FullName, LogLevel);
            loggingBuilder.SetMinimumLevel(LogLevel);
        });

        services.AddApplicationInsightsTelemetryWorkerService(options =>
        {
            options.ConnectionString = $"InstrumentationKey={instrumentationKey}";
        });
    }

    private static IKernel GetKernel(ILogger logger)
    {
        string folder = RepoFiles.SampleSkillsPath();

        var kernel = new KernelBuilder()
            .WithLogger(logger)
            .WithAzureChatCompletionService(
                Env.Var("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                Env.Var("AZURE_OPENAI_CHAT_ENDPOINT"),
                Env.Var("AZURE_OPENAI_CHAT_KEY"))
            .Build();

        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill", "WriterSkill");

        return kernel;
    }

    private static ISequentialPlanner GetPlanner(IKernel kernel, ILogger logger, int maxTokens = 1024)
    {
        var plannerConfig = new SequentialPlannerConfig { MaxTokens = maxTokens };

        return SequentialPlannerFactory
            .GetPlanner(kernel, plannerConfig)
            .WithInstrumentation(logger);
    }
}
