// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Text;
using System.Text.Json.Serialization;
using Azure.Monitor.OpenTelemetry.Exporter;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Extensions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenTelemetry;
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

namespace Telemetry;

/// <summary>
/// This sample collects telemetry for function call when using AzureOpenAI.
/// </summary>
/// <remarks>
/// You can configure the sample to run with whatever models you want to test.
/// The sample will enable telemetry for the Semantic Kernel using Application Insights.
/// When you run the sample each test will output an Operation Id.
/// In your Application Insights instance go to Investigate -> Transaction search and enter the operation id.
/// Select the first entry and then select the "View timeline" to see all of the chat completions and function calls.
/// </remarks>
public sealed class AzureOpenAI_FunctionCallingTelemetry(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Sample showing how to run a function calling test for different AzureOpenAI deployments with the specified number of attempts.
    /// For this sample auto function calling is invoked and it is expected that the provided function will always be called by the model.
    /// The test checks the response to verify that the model has invoked the function as expected.
    /// </summary>
    /// <remarks>
    /// A plugin is provided which includes a <see cref="WidgetFactory.CreateWidget(WidgetType, WidgetColor[])"/> function.
    /// This function can create widget of a particular <see cref="WidgetType"/> and <see cref="WidgetColor"/>.
    /// The function is provided to the model and the model is prompted to create a widget with a supported type and color.
    /// </remarks>
    /// <param name="deploymentName">The name of the AzureOpenAI deployment.</param>
    /// <param name="attempts">The number of times to invoke the prompt.</param>
    /// <param name="stream">Flag indicating whether or not to use streaming.</param>
    [Theory]
    [InlineData("gpt-4o", 10, true)]
    [InlineData("gpt-4", 10, true)]
    public async Task VerifyAzureOpenAIFunctionCallingResultAsync(string deploymentName, int attempts, bool stream)
    {
        // Enable model diagnostics with sensitive data.
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

        // Implement tracing and metering
        var connectionString = TestConfiguration.ApplicationInsights.ConnectionString;
        var resourceBuilder = ResourceBuilder
            .CreateDefault()
            .AddService("OpenAI_FunctionCallingTelemetry");
        using var traceProvider = Sdk.CreateTracerProviderBuilder()
            .SetResourceBuilder(resourceBuilder)
            .AddSource("Microsoft.SemanticKernel*")
            .AddSource("System.Net.Http*")
            .AddSource("OpenAI_FunctionCallingTelemetry")
            .AddAzureMonitorTraceExporter(options => options.ConnectionString = connectionString)
            .Build();
        using var meterProvider = Sdk.CreateMeterProviderBuilder()
            .SetResourceBuilder(resourceBuilder)
            .AddMeter("Microsoft.SemanticKernel*")
            .AddAzureMonitorMetricExporter(options => options.ConnectionString = connectionString)
            .Build();
        using var loggerFactory = Microsoft.Extensions.Logging.LoggerFactory.Create(builder =>
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
            builder.SetMinimumLevel(LogLevel.Information);
        });

        // Create filters to add function calling meters
        var functionFilter = new FunctionInvocationFilter();

        // Create a kernel with an Azure OpenAI chat completion service 
        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.Services.AddSingleton(loggerFactory);
        kernelBuilder.Services.AddSingleton<IFunctionInvocationFilter>(functionFilter);
        kernelBuilder.AddAzureOpenAIChatCompletion(
                deploymentName: deploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey);
        kernelBuilder.Plugins.AddFromType<WidgetFactory>();
        Kernel kernel = kernelBuilder.Build();
        kernel.Data["TargetService"] = "AzureOpenAI";

        using var activity = s_activitySource.StartActivity("Main");
        Console.WriteLine($"Operation Id: {Activity.Current?.TraceId}");
        if (stream)
        {
            await VerifyFunctionCallStreamingAsync(kernel, attempts, functionFilter);
        }
        else
        {
            await VerifyFunctionCallAsync(kernel, attempts, functionFilter);
        }
    }

    #region private
    private static readonly ActivitySource s_activitySource = new("OpenAI_FunctionCallingTelemetry");

    /// <summary>
    /// Verify function calling using the provided <see cref="Kernel"/>.
    /// </summary>
    private async Task VerifyFunctionCallAsync(Kernel kernel, int attempts, FunctionInvocationFilter functionFilter)
    {
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();
        ChatHistory chatHistory = [];
        int success = 0;
        Random random = new();
        Array widgetColors = Enum.GetValues<WidgetColor>();
        Array widgetTypes = Enum.GetValues<WidgetType>();
        for (var attempt = 0; attempt < attempts; attempt++)
        {
            var widgetColor = (WidgetColor)widgetColors.GetValue(random.Next(widgetColors.Length))!;
            var widgetType = (WidgetType)widgetTypes.GetValue(random.Next(widgetTypes.Length))!;

            chatHistory.AddUserMessage($"Create a {widgetType} {widgetColor} colored widget for me.");
            var result = await chatService.GetChatMessageContentsAsync(chatHistory, settings, kernel);

            var resultStr = result.ToString();
            if (
                resultStr is not null &&
                resultStr.Contains(widgetColor.ToString(), StringComparison.OrdinalIgnoreCase) && // Expect the color to be in the result
                resultStr.Contains(widgetType.ToString(), StringComparison.OrdinalIgnoreCase)) // Expect the type to be in the result
            {
                success++;
            }
        }
        Assert.Equal(attempts, success);
    }

    /// <summary>
    /// Verify function calling using the provided <see cref="Kernel"/>.
    /// </summary>
    private async Task VerifyFunctionCallStreamingAsync(Kernel kernel, int attempts, FunctionInvocationFilter functionFilter)
    {
        OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };
        IChatCompletionService chatService = kernel.GetRequiredService<IChatCompletionService>();
        ChatHistory chatHistory = [];
        int success = 0;
        Random random = new();
        Array widgetColors = Enum.GetValues<WidgetColor>();
        Array widgetTypes = Enum.GetValues<WidgetType>();
        for (var attempt = 0; attempt < attempts; attempt++)
        {
            var widgetColor = (WidgetColor)widgetColors.GetValue(random.Next(widgetColors.Length))!;
            var widgetType = (WidgetType)widgetTypes.GetValue(random.Next(widgetTypes.Length))!;

            chatHistory.AddUserMessage($"Create a {widgetType} {widgetColor} colored widget for me.");
            var results = chatService.GetStreamingChatMessageContentsAsync(chatHistory, settings, kernel);

            var resultBuilder = new StringBuilder();
            await foreach (StreamingKernelContent update in results)
            {
                resultBuilder.Append(update);
            }

            var resultStr = resultBuilder.ToString();
            chatHistory.AddAssistantMessage(resultStr);

            if (
                resultStr.Contains(widgetColor.ToString(), StringComparison.OrdinalIgnoreCase) && // Expect the color to be in the result
                resultStr.Contains(widgetType.ToString(), StringComparison.OrdinalIgnoreCase)) // Expect the type to be in the result
            {
                success++;
            }
        }
        Assert.Equal(attempts, success);
    }

    /// <summary>
    /// A plugin that creates widgets.
    /// </summary>
    private sealed class WidgetFactory
    {
        [KernelFunction]
        [Description("Creates a new widget of the specified type and colors")]
        public WidgetDetails CreateWidget([Description("The type of widget to be created")] WidgetType widgetType, [Description("The colors of the widget to be created")] WidgetColor[] widgetColors)
        {
            var colors = string.Join('-', widgetColors.Select(c => c.GetDisplayName()).ToArray());
            return new()
            {
                SerialNumber = $"{widgetType}-{colors}-{Guid.NewGuid()}",
                Type = widgetType,
                Colors = widgetColors
            };
        }
    }

    /// <summary>
    /// A <see cref="JsonConverter"/> is required to correctly convert enum values.
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    private enum WidgetType
    {
        [Description("A widget that is useful.")]
        Useful,

        [Description("A widget that is decorative.")]
        Decorative
    }

    /// <summary>
    /// A <see cref="JsonConverter"/> is required to correctly convert enum values.
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    private enum WidgetColor
    {
        [Description("Use when creating a red item.")]
        Red,

        [Description("Use when creating a green item.")]
        Green,

        [Description("Use when creating a blue item.")]
        Blue
    }

    /// <summary>
    /// Represents the details associated with a Widget.
    /// </summary>
    private sealed class WidgetDetails
    {
        public string SerialNumber { get; init; }
        public WidgetType Type { get; init; }
        public WidgetColor[] Colors { get; init; }
    }

    /// <summary>Adds a counter for all function invocations.</summary>
    private sealed class FunctionInvocationFilter : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            var functionName = context.Function.Name;

            var meter = new Meter("Microsoft.SemanticKernel");

            var functionCallCounter = meter.CreateCounter<int>("semantic_kernel.function.invocation.count");
            functionCallCounter.Add(1, KeyValuePair.Create<string, object?>("function_name", functionName));

            await next(context);
        }
    }

    #endregion
}
