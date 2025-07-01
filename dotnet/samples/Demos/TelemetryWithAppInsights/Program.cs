// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Azure.Identity;
using Azure.Monitor.OpenTelemetry.Exporter;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Connectors.MistralAI;
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
        using (var _ = s_activitySource.StartActivity("Chat"))
        {
            await RunAzureAIInferenceChatAsync(kernel);
            Console.WriteLine();
            await RunAzureOpenAIChatAsync(kernel);
            Console.WriteLine();
            await RunGoogleAIChatAsync(kernel);
            Console.WriteLine();
            await RunHuggingFaceChatAsync(kernel);
            Console.WriteLine();
            await RunMistralAIChatAsync(kernel);
        }

        Console.WriteLine();
        Console.WriteLine();

        Console.WriteLine("Get weather.");
        using (var _ = s_activitySource.StartActivity("ToolCalls"))
        {
            await RunAzureOpenAIToolCallsAsync(kernel);
            Console.WriteLine();
        }
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

    private const string AzureOpenAIServiceKey = "AzureOpenAI";
    private const string GoogleAIGeminiServiceKey = "GoogleAIGemini";
    private const string HuggingFaceServiceKey = "HuggingFace";
    private const string MistralAIServiceKey = "MistralAI";
    private const string AzureAIInferenceServiceKey = "AzureAIInference";

    #region chat completion

    private static async Task RunAzureAIInferenceChatAsync(Kernel kernel)
    {
        Console.WriteLine("============= Azure AI Inference Chat Completion =============");

        if (TestConfiguration.AzureAIInference is null)
        {
            Console.WriteLine("Azure AI Inference is not configured. Skipping.");
            return;
        }

        using var activity = s_activitySource.StartActivity(AzureAIInferenceServiceKey);
        SetTargetService(kernel, AzureAIInferenceServiceKey);
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

    private static async Task RunAzureOpenAIChatAsync(Kernel kernel)
    {
        Console.WriteLine("============= Azure OpenAI Chat Completion =============");

        if (TestConfiguration.AzureOpenAI is null)
        {
            Console.WriteLine("Azure OpenAI is not configured. Skipping.");
            return;
        }

        using var activity = s_activitySource.StartActivity(AzureOpenAIServiceKey);
        SetTargetService(kernel, AzureOpenAIServiceKey);
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

        if (TestConfiguration.GoogleAI is null)
        {
            Console.WriteLine("Google AI is not configured. Skipping.");
            return;
        }

        using var activity = s_activitySource.StartActivity(GoogleAIGeminiServiceKey);
        SetTargetService(kernel, GoogleAIGeminiServiceKey);

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

        if (TestConfiguration.HuggingFace is null)
        {
            Console.WriteLine("Hugging Face is not configured. Skipping.");
            return;
        }

        using var activity = s_activitySource.StartActivity(HuggingFaceServiceKey);
        SetTargetService(kernel, HuggingFaceServiceKey);

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

    private static async Task RunMistralAIChatAsync(Kernel kernel)
    {
        Console.WriteLine("============= MistralAI Chat Completion =============");

        if (TestConfiguration.MistralAI is null)
        {
            Console.WriteLine("Mistral AI is not configured. Skipping.");
            return;
        }

        using var activity = s_activitySource.StartActivity(MistralAIServiceKey);
        SetTargetService(kernel, MistralAIServiceKey);

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
        // Create the plugin from the sample plugins folder without registering it to the kernel.
        // We do not advise registering plugins to the kernel and then invoking them directly,
        // especially when the service supports function calling. Doing so will cause unexpected behavior,
        // such as repeated calls to the same function.
        var folder = RepoFiles.SamplePluginsPath();
        var plugin = kernel.CreatePluginFromPromptDirectory(Path.Combine(folder, "WriterPlugin"));

        // Using non-streaming to get the poem.
        var poem = await kernel.InvokeAsync<string>(
            plugin["ShortPoem"],
            new KernelArguments { ["input"] = "Write a poem about John Doe." });
        Console.WriteLine($"Poem:\n{poem}\n");

        // Use streaming to translate the poem.
        Console.WriteLine("Translated Poem:");
        await foreach (var update in kernel.InvokeStreamingAsync<string>(
            plugin["Translate"],
            new KernelArguments
            {
                ["input"] = poem,
                ["language"] = "Italian"
            }))
        {
            Console.Write(update);
        }
    }
    #endregion

    #region tool calls
    private static async Task RunAzureOpenAIToolCallsAsync(Kernel kernel)
    {
        Console.WriteLine("============= Azure OpenAI ToolCalls =============");

        if (TestConfiguration.AzureOpenAI is null)
        {
            Console.WriteLine("Azure OpenAI is not configured. Skipping.");
            return;
        }

        using var activity = s_activitySource.StartActivity(AzureOpenAIServiceKey);
        SetTargetService(kernel, AzureOpenAIServiceKey);
        try
        {
            await RunAutoToolCallAsync(kernel);
        }
        catch (Exception ex)
        {
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            Console.WriteLine($"Error: {ex.Message}");
        }
    }

    private static async Task RunAutoToolCallAsync(Kernel kernel)
    {
        var result = await kernel.InvokePromptAsync("What is the weather like in my location?");

        Console.WriteLine(result);
    }
    #endregion

    private static Kernel GetKernel(ILoggerFactory loggerFactory)
    {
        var folder = RepoFiles.SamplePluginsPath();

        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.Services.AddSingleton(loggerFactory);

        if (TestConfiguration.AzureOpenAI is not null)
        {
            if (TestConfiguration.AzureOpenAI.ApiKey is not null)
            {
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                    modelId: TestConfiguration.AzureOpenAI.ChatModelId,
                    endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                    apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                    serviceId: AzureOpenAIServiceKey);
            }
            else
            {
                builder.AddAzureOpenAIChatCompletion(
                    deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                    modelId: TestConfiguration.AzureOpenAI.ChatModelId,
                    endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                    credentials: new AzureCliCredential(),
                    serviceId: AzureOpenAIServiceKey);
            }
        }

        if (TestConfiguration.GoogleAI is not null)
        {
            builder.AddGoogleAIGeminiChatCompletion(
                modelId: TestConfiguration.GoogleAI.Gemini.ModelId,
                apiKey: TestConfiguration.GoogleAI.ApiKey,
                serviceId: GoogleAIGeminiServiceKey);
        }

        if (TestConfiguration.HuggingFace is not null)
        {
            builder.AddHuggingFaceChatCompletion(
                model: TestConfiguration.HuggingFace.ModelId,
                endpoint: new Uri("https://api-inference.huggingface.co"),
                apiKey: TestConfiguration.HuggingFace.ApiKey,
                serviceId: HuggingFaceServiceKey);
        }

        if (TestConfiguration.MistralAI is not null)
        {
            builder.AddMistralChatCompletion(
                modelId: TestConfiguration.MistralAI.ChatModelId,
                apiKey: TestConfiguration.MistralAI.ApiKey,
                serviceId: MistralAIServiceKey);
        }

        if (TestConfiguration.AzureAIInference is not null)
        {
            if (string.IsNullOrEmpty(TestConfiguration.AzureAIInference.ApiKey))
            {
                builder.AddAzureAIInferenceChatCompletion(
                    modelId: TestConfiguration.AzureAIInference.ModelId,
                    credential: new DefaultAzureCredential(),
                    endpoint: TestConfiguration.AzureAIInference.Endpoint,
                    serviceId: AzureAIInferenceServiceKey,
                    openTelemetrySourceName: "Telemetry.Example",
                    openTelemetryConfig: c => c.EnableSensitiveData = true);
            }
            else
            {
                builder.AddAzureAIInferenceChatCompletion(
                    modelId: TestConfiguration.AzureAIInference.ModelId,
                    apiKey: TestConfiguration.AzureAIInference.ApiKey,
                    endpoint: TestConfiguration.AzureAIInference.Endpoint,
                    serviceId: AzureAIInferenceServiceKey,
                    openTelemetrySourceName: "Telemetry.Example",
                    openTelemetryConfig: c => c.EnableSensitiveData = true);
            }
        }

        builder.Services.AddSingleton<IAIServiceSelector>(new AIServiceSelector());
        builder.Plugins.AddFromType<WeatherPlugin>();
        builder.Plugins.AddFromType<LocationPlugin>();

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
                        AzureOpenAIServiceKey => new OpenAIPromptExecutionSettings()
                        {
                            Temperature = 0,
                            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
                        },
                        GoogleAIGeminiServiceKey => new GeminiPromptExecutionSettings()
                        {
                            Temperature = 0,
                            // Not show casing the AutoInvokeKernelFunctions behavior for Gemini due the following issue:
                            // https://github.com/microsoft/semantic-kernel/issues/6282
                            // ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions
                        },
                        HuggingFaceServiceKey => new HuggingFacePromptExecutionSettings()
                        {
                            Temperature = 0,
                        },
                        MistralAIServiceKey => new MistralAIPromptExecutionSettings()
                        {
                            Temperature = 0,
                            ToolCallBehavior = MistralAIToolCallBehavior.AutoInvokeKernelFunctions
                        },
                        AzureAIInferenceServiceKey => new AzureAIInferencePromptExecutionSettings()
                        {
                            Temperature = 0,

                            // Function/Tool calling enabled models in Azure AI Inference are listed in the below page as "Tool calling: Yes/No"
                            // https://learn.microsoft.com/en-us/azure/ai-foundry/model-inference/concepts/models, 
                            // Ensure your model support tool calling before enabling the setting below.

                            // FunctionChoiceBehavior = FunctionChoiceBehavior.Auto()
                        },
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

    #region Plugins

    public sealed class WeatherPlugin
    {
        [KernelFunction]
        public string GetWeather(string location) => $"Weather in {location} is 70°F.";
    }

    public sealed class LocationPlugin
    {
        [KernelFunction]
        public string GetCurrentLocation()
        {
            return "Seattle";
        }
    }

    #endregion
}
