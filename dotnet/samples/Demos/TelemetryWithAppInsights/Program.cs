// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Azure.Monitor.OpenTelemetry.Exporter;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Services;
using OpenTelemetry;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

/// <summary>
/// Example of telemetry in Semantic Kernel using Application Insights within console application.
/// </summary>
public sealed class Program
{
    /// <summary>
    /// The main entry point for the application.
    /// </summary>
    /// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
    public static async Task Main()
    {
        // Enable model diagnostics with sensitive data.
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

        // Load configuration from environment variables or user secrets.
        LoadUserSecrets();

        var connectionString = TestConfiguration.ApplicationInsights.ConnectionString;
        var resourceBuilder = ResourceBuilder
            .CreateDefault()
            .AddService("TelemetryExample");

        using var traceProvider = Sdk.CreateTracerProviderBuilder()
            .SetResourceBuilder(resourceBuilder)
            .AddSource("Microsoft.SemanticKernel*")
            .AddSource("Telemetry.Example")
            .AddAzureMonitorTraceExporter(options => options.ConnectionString = connectionString)
            .Build();

        using var meterProvider = Sdk.CreateMeterProviderBuilder()
            .SetResourceBuilder(resourceBuilder)
            .AddMeter("Microsoft.SemanticKernel*")
            .AddAzureMonitorMetricExporter(options => options.ConnectionString = connectionString)
            .Build();

        using var loggerFactory = LoggerFactory.Create(builder =>
        {
            // Add OpenTelemetry as a logging provider
            builder.AddOpenTelemetry(options =>
            {
                options.SetResourceBuilder(resourceBuilder);
                options.AddAzureMonitorLogExporter(options => options.ConnectionString = connectionString);
                // Format log messages. This is default to false.
                options.IncludeFormattedMessage = true;
                options.IncludeScopes = true;
            });
            builder.SetMinimumLevel(MinLogLevel);
        });

        var kernel = GetKernel(loggerFactory);

        using var activity = s_activitySource.StartActivity("Main");
        Console.WriteLine($"Operation/Trace ID: {Activity.Current?.TraceId}");
        Console.WriteLine();

        Console.WriteLine("Write a poem about John Doe and translate it to Italian.");
        await RunAzureOpenAIChatAsync(kernel);
        Console.WriteLine();
        await RunGoogleAIChatAsync(kernel);
        Console.WriteLine();
        await RunHuggingFaceChatAsync(kernel);
    }

    #region Private
    /// <summary>
    /// Log level to be used by <see cref="ILogger"/>.
    /// </summary>
    /// <remarks>
    /// <see cref="LogLevel.Information"/> is set by default. <para />
    /// <see cref="LogLevel.Trace"/> will enable logging with more detailed information, including sensitive data. Should not be used in production. <para />
    /// </remarks>
    private const LogLevel MinLogLevel = LogLevel.Information;

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for the application activities.
    /// </summary>
    private static readonly ActivitySource s_activitySource = new("Telemetry.Example");

    private const string AzureOpenAIChatServiceKey = "AzureOpenAIChat";
    private const string GoogleAIGeminiChatServiceKey = "GoogleAIGeminiChat";
    private const string HuggingFaceChatServiceKey = "HuggingFaceChat";

    private static async Task RunAzureOpenAIChatAsync(Kernel kernel)
    {
        Console.WriteLine("============= Azure OpenAI Chat Completion =============");

        using var activity = s_activitySource.StartActivity(AzureOpenAIChatServiceKey);
        SetTargetService(kernel, AzureOpenAIChatServiceKey);
        try
        {
            await RunChatAsync(kernel);
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            Console.WriteLine($"Error: {ex.Message}");
        }
    }

    private static async Task RunGoogleAIChatAsync(Kernel kernel)
    {
        Console.WriteLine("============= Google Gemini Chat Completion =============");

        using var activity = s_activitySource.StartActivity(GoogleAIGeminiChatServiceKey);
        SetTargetService(kernel, GoogleAIGeminiChatServiceKey);

        try
        {
            await RunChatAsync(kernel);
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            Console.WriteLine($"Error: {ex.Message}");
        }
    }

    private static async Task RunHuggingFaceChatAsync(Kernel kernel)
    {
        Console.WriteLine("============= HuggingFace Chat Completion =============");

        using var activity = s_activitySource.StartActivity(HuggingFaceChatServiceKey);
        SetTargetService(kernel, HuggingFaceChatServiceKey);

        try
        {
            await RunChatAsync(kernel);
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            Console.WriteLine($"Error: {ex.Message}");
        }
    }

    private static async Task RunChatAsync(Kernel kernel)
    {
        var poem = await kernel.InvokeAsync<string>(
            "WriterPlugin",
            "ShortPoem",
            new KernelArguments { ["input"] = "Write a poem about John Doe." });
        var translatedPoem = await kernel.InvokeAsync<string>(
            "WriterPlugin",
            "Translate",
            new KernelArguments
            {
                ["input"] = poem,
                ["language"] = "Italian"
            });

        Console.WriteLine($"Poem:\n{poem}\n\nTranslated Poem:\n{translatedPoem}");
    }

    private static Kernel GetKernel(ILoggerFactory loggerFactory)
    {
        var folder = RepoFiles.SamplePluginsPath();

        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(loggerFactory);
        builder
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                serviceId: AzureOpenAIChatServiceKey)
            .AddGoogleAIGeminiChatCompletion(
                modelId: TestConfiguration.GoogleAI.Gemini.ModelId,
                apiKey: TestConfiguration.GoogleAI.ApiKey,
                serviceId: GoogleAIGeminiChatServiceKey)
            .AddHuggingFaceChatCompletion(
                model: TestConfiguration.HuggingFace.ModelId,
                endpoint: new Uri("https://api-inference.huggingface.co"),
                apiKey: TestConfiguration.HuggingFace.ApiKey,
                serviceId: HuggingFaceChatServiceKey);

        builder.Services.AddSingleton<IAIServiceSelector>(new AIServiceSelector());
        builder.Plugins.AddFromPromptDirectory(Path.Combine(folder, "WriterPlugin"));

        return builder.Build();
    }

    private static void SetTargetService(Kernel kernel, string targetServiceKey)
    {
        if (kernel.Data.ContainsKey("TargetService"))
        {
            kernel.Data["TargetService"] = targetServiceKey;
        }
        else
        {
            kernel.Data.Add("TargetService", targetServiceKey);
        }
    }

    private static void LoadUserSecrets()
    {
        IConfigurationRoot configRoot = new ConfigurationBuilder()
            .AddEnvironmentVariables()
            .AddUserSecrets<Program>()
            .Build();
        TestConfiguration.Initialize(configRoot);
    }

    private sealed class AIServiceSelector : IAIServiceSelector
    {
        public bool TrySelectAIService<T>(
            Kernel kernel, KernelFunction function, KernelArguments arguments,
            [NotNullWhen(true)] out T? service, out PromptExecutionSettings? serviceSettings) where T : class, IAIService
        {
            var targetServiceKey = kernel.Data.TryGetValue("TargetService", out object? value) ? value : null;
            if (targetServiceKey is not null)
            {
                var targetService = kernel.Services.GetKeyedServices<T>(targetServiceKey).FirstOrDefault();
                if (targetService is not null)
                {
                    service = targetService;
                    serviceSettings = targetServiceKey switch
                    {
                        AzureOpenAIChatServiceKey => new OpenAIPromptExecutionSettings(),
                        GoogleAIGeminiChatServiceKey => new GeminiPromptExecutionSettings(),
                        HuggingFaceChatServiceKey => new HuggingFacePromptExecutionSettings(),
                        _ => null,
                    };

                    return true;
                }
            }

            service = null;
            serviceSettings = null;
            return false;
        }
    }
    #endregion
}
