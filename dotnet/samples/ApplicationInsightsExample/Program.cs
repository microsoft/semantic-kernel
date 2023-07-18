// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading.Tasks;
using Microsoft.ApplicationInsights;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.ApplicationInsights.Extensibility;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.ApplicationInsights;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Example of telemetry in Semantic Kernel using Application Insights within console application.
/// </summary>
public sealed class Program
{
    /// <summary>
    /// Log level to be used by <see cref="ILogger"/>.
    /// </summary>
    /// <remarks>
    /// <see cref="LogLevel.Information"/> is set by default. <para />
    /// <see cref="LogLevel.Trace"/> will enable logging with more detailed information, including sensitive data. Should not be used in production. <para />
    /// </remarks>
    private static LogLevel LogLevel = LogLevel.Information;

    public static async Task Main()
    {
        var serviceProvider = GetServiceProvider();

        var telemetryClient = serviceProvider.GetRequiredService<TelemetryClient>();
        var logger = serviceProvider.GetRequiredService<ILogger<Program>>();

        using var meterListener = GetMeterListener(telemetryClient);
        using var activityListener = GetActivityListener(telemetryClient);

        var kernel = GetKernel(logger, meterListener, activityListener);
        var planner = GetPlanner(kernel, logger);

        try
        {
            using var operation = telemetryClient.StartOperation<DependencyTelemetry>("ApplicationInsights.Example");

            Console.WriteLine("Operation/Trace ID:");
            Console.WriteLine(Activity.Current?.TraceId);

            var plan = await planner.CreatePlanAsync("Write a poem about John Doe, then translate it into Italian.");

            Console.WriteLine("Original plan:");
            Console.WriteLine(plan.ToPlanString());

            var result = await kernel.RunAsync(plan);

            Console.WriteLine("Result:");
            Console.WriteLine(result.Result);
        }
        finally
        {
            // Explicitly call Flush() followed by sleep is required in console apps.
            // This is to ensure that even if application terminates, telemetry is sent to the back-end.
            telemetryClient.Flush();
            await Task.Delay(5000);
        }
    }

    private static ServiceProvider GetServiceProvider()
    {
        var services = new ServiceCollection();

        ConfigureApplicationInsightsTelemetry(services);

        return services.BuildServiceProvider();
    }

    private static void ConfigureApplicationInsightsTelemetry(ServiceCollection services)
    {
        string instrumentationKey = Env.Var("ApplicationInsights__InstrumentationKey");

        services.AddLogging(loggingBuilder =>
        {
            loggingBuilder.AddFilter<ApplicationInsightsLoggerProvider>(typeof(Program).FullName, LogLevel);
            loggingBuilder.SetMinimumLevel(LogLevel);
        });

        services.AddApplicationInsightsTelemetryWorkerService(options =>
        {
            options.ConnectionString = $"InstrumentationKey={instrumentationKey}";
        });
    }

    private static IKernel GetKernel(ILogger logger, MeterListener meterListener, ActivityListener activityListener)
    {
        string folder = RepoFiles.SampleSkillsPath();

        var kernel = new KernelBuilder()
            .WithLogging(logger)
            .WithMetering(meterListener)
            .WithTracing(activityListener)
            .WithAzureChatCompletionService(
                Env.Var("AzureOpenAI__ChatDeploymentName"),
                Env.Var("AzureOpenAI__Endpoint"),
                Env.Var("AzureOpenAI__ApiKey"))
            .Build();

        kernel.ImportSemanticSkillFromDirectory(folder, "SummarizeSkill", "WriterSkill");

        return kernel;
    }

    private static ISequentialPlanner GetPlanner(
        IKernel kernel,
        ILogger logger,
        int maxTokens = 1024)
    {
        var plannerConfig = new SequentialPlannerConfig { MaxTokens = maxTokens };

        return new SequentialPlannerBuilder(kernel)
            .WithConfiguration(plannerConfig)
            .WithLogging(logger)
            .Build();
    }

    /// <summary>
    /// Example of metering configuration in Application Insights
    /// using <see cref="MeterListener"/> to attach for <see cref="Meter"/> recordings.
    /// </summary>
    /// <param name="telemetryClient">Instance of Application Insights <see cref="TelemetryClient"/>.</param>
    private static MeterListener GetMeterListener(TelemetryClient telemetryClient)
    {
        var meterListener = new MeterListener();

        MeasurementCallback<double> measurementCallback = (instrument, measurement, tags, state) =>
        {
            telemetryClient.GetMetric(instrument.Name).TrackValue(measurement);
        };

        meterListener.SetMeasurementEventCallback(measurementCallback);

        return meterListener;
    }

    /// <summary>
    /// Example of advanced distributed tracing configuration in Application Insights
    /// using <see cref="ActivityListener"/> to attach for <see cref="Activity"/> events.
    /// </summary>
    /// <param name="telemetryClient">Instance of Application Insights <see cref="TelemetryClient"/>.</param>
    private static ActivityListener GetActivityListener(TelemetryClient telemetryClient)
    {
        var operations = new ConcurrentDictionary<string, IOperationHolder<DependencyTelemetry>>();

        // For more detailed tracing we need to attach Activity entity to Application Insights operation manually.
        Action<Activity> activityStarted = activity =>
        {
            var operation = telemetryClient.StartOperation<DependencyTelemetry>(activity);
            operation.Telemetry.Type = activity.Kind.ToString();

            operations.TryAdd(activity.TraceId.ToString(), operation);
        };

        // We also need to manually stop Application Insights operation when Activity entity is stopped.
        Action<Activity> activityStopped = activity =>
        {
            if (operations.TryRemove(activity.TraceId.ToString(), out var operation))
            {
                telemetryClient.StopOperation(operation);
            }
        };

        return new ActivityListener()
        {
            Sample = (ref ActivityCreationOptions<ActivityContext> _) => ActivitySamplingResult.AllData,
            SampleUsingParentId = (ref ActivityCreationOptions<string> _) => ActivitySamplingResult.AllData,
            ActivityStarted = activityStarted,
            ActivityStopped = activityStopped
        };
    }
}
