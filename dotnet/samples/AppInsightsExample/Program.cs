// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.ApplicationInsights;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.ApplicationInsights;

namespace AppInsightsExample;

public sealed class Program
{
    public static void Main()
    {
        var serviceProvider = GetServiceProvider();

        var logger = serviceProvider.GetRequiredService<ILogger<Program>>();

        var telemetryClient = serviceProvider.GetRequiredService<TelemetryClient>();

        logger.LogInformation("This is test information message.");

        // Explicitly call Flush() followed by sleep is required in console apps.
        // This is to ensure that even if application terminates, telemetry is sent to the back-end.
        telemetryClient.Flush();
        Task.Delay(5000).Wait();
    }

    private static ServiceProvider GetServiceProvider()
    {
        var services = new ServiceCollection();

        ConfigureLogging(services);

        return services.BuildServiceProvider();
    }

    private static void ConfigureLogging(ServiceCollection services)
    {
        const string instrumentationKey = "<instrumentation_key>";

        services.AddLogging(loggingBuilder =>
        {
            loggingBuilder.AddFilter<ApplicationInsightsLoggerProvider>(typeof(Program).FullName, LogLevel.Trace);
            loggingBuilder.SetMinimumLevel(LogLevel.Trace);
        });

        services.AddApplicationInsightsTelemetryWorkerService(options =>
        {
            options.ConnectionString = $"InstrumentationKey={instrumentationKey}";
        });
    }
}
