// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Text;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Filtering;

/// <summary>
/// Kernel and connectors have out-of-the-box telemetry to capture key information, which is available during requests.
/// In most cases this telemetry should be enough to understand how the application behaves.
/// This example contains the same telemetry recreated using Filters.
/// This should allow to extend existing telemetry if needed with additional information and have the same set of logging messages for custom connectors.
/// </summary>
public class TelemetryWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task LoggingAsync(bool isStreaming)
    {
        // Initialize kernel with chat completion service.
        var builder = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey);

        // Create and add logger, which will output messages to test detail summary window.
        var logger = this.LoggerFactory.CreateLogger<TelemetryWithFilters>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add filters with logging.
        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionInvocationLoggingFilter>();
        builder.Services.AddSingleton<IPromptRenderFilter, PromptRenderLoggingFilter>();
        builder.Services.AddSingleton<IAutoFunctionInvocationFilter, AutoFunctionInvocationLoggingFilter>();

        var kernel = builder.Build();

        // Import sample functions.
        kernel.ImportPluginFromFunctions("HelperFunctions",
        [
            kernel.CreateFunctionFromMethod(() => DateTime.UtcNow.ToString("R"), "GetCurrentUtcTime", "Retrieves the current time in UTC."),
            kernel.CreateFunctionFromMethod((string cityName) =>
                cityName switch
                {
                    "Boston" => "61 and rainy",
                    "London" => "55 and cloudy",
                    "Miami" => "80 and sunny",
                    "Paris" => "60 and rainy",
                    "Tokyo" => "50 and sunny",
                    "Sydney" => "75 and sunny",
                    "Tel Aviv" => "80 and sunny",
                    _ => "31 and snowing",
                }, "GetWeatherForCity", "Gets the current weather for the specified city"),
        ]);

        // Enable automatic function calling.
        var executionSettings = new OpenAIPromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(),
            ModelId = "gpt-4"
        };

        // Define custom transaction ID to group set of operations related to the request.
        var transactionId = new Guid("2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2");

        // Note: logging scopes are available for out-of-the-box SK telemetry as well.
        using (logger.BeginScope($"Transaction ID: [{transactionId}]"))
        {
            // Invoke prompt with arguments.
            const string Prompt = "Given the current time of day and weather, what is the likely color of the sky in {{$city}}?";

            var arguments = new KernelArguments(executionSettings) { ["city"] = "Boston" };

            if (isStreaming)
            {
                await foreach (var item in kernel.InvokePromptStreamingAsync<StreamingChatMessageContent>(Prompt, arguments))
                {
                    if (item.Content is not null)
                    {
                        Console.Write(item.Content);
                    }
                }
            }
            else
            {
                var result = await kernel.InvokePromptAsync(Prompt, arguments);

                Console.WriteLine(result);
            }
        }

        // Output:
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function InvokePromptAsync_Id invoking.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function arguments: {"city":"Boston"}
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Execution settings: {"default":{"service_id":null,"model_id":"gpt-4"}}
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Rendered prompt: Given the current time of day and weather, what is the likely color of the sky in Boston?
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] ChatHistory: [{"Role":{"Label":"user"},...
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function count: 1
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function call requests: HelperFunctions-GetCurrentUtcTime({})
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function GetCurrentUtcTime invoking.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function GetCurrentUtcTime succeeded.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function result: Tue, 25 Jun 2024 15:30:16 GMT
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function completed. Duration: 0.0011554s
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] ChatHistory: [{"Role":{"Label":"user"},...
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function count: 1
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function call requests: HelperFunctions-GetWeatherForCity({"cityName":"Boston"})
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function GetWeatherForCity invoking.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function arguments: {"cityName":"Boston"}
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function GetWeatherForCity succeeded.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function result: 61 and rainy
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function completed. Duration: 0.0020878s
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function InvokePromptAsync_Id succeeded.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function result: The sky in Boston would likely be gray due to the rain and current time of day.
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Usage: {"CompletionTokens":19,"PromptTokens":169,"TotalTokens":188}
        // Transaction ID: [2d9ca2ce-8bf7-4d43-9f90-05eda7122aa2] Function completed. Duration: 5.397173s
    }

    /// <summary>
    /// Filter which logs an information available during function invocation such as:
    /// Function name, arguments, execution settings, result, duration, token usage.
    /// </summary>
    private sealed class FunctionInvocationLoggingFilter(ILogger logger) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            long startingTimestamp = Stopwatch.GetTimestamp();

            logger.LogInformation("Function {FunctionName} invoking.", context.Function.Name);

            if (context.Arguments.Count > 0)
            {
                logger.LogTrace("Function arguments: {Arguments}", JsonSerializer.Serialize(context.Arguments));
            }

            if (logger.IsEnabled(LogLevel.Information) && context.Arguments.ExecutionSettings is not null)
            {
                logger.LogInformation("Execution settings: {Settings}", JsonSerializer.Serialize(context.Arguments.ExecutionSettings));
            }

            try
            {
                await next(context);

                logger.LogInformation("Function {FunctionName} succeeded.", context.Function.Name);

                if (context.IsStreaming)
                {
                    // Overriding the result in a streaming scenario enables the filter to stream chunks 
                    // back to the operation's origin without interrupting the data flow.
                    var enumerable = context.Result.GetValue<IAsyncEnumerable<StreamingChatMessageContent>>();
                    context.Result = new FunctionResult(context.Result, ProcessFunctionResultStreamingAsync(enumerable!));
                }
                else
                {
                    ProcessFunctionResult(context.Result);
                }
            }
            catch (Exception exception)
            {
                logger.LogError(exception, "Function failed. Error: {Message}", exception.Message);
                throw;
            }
            finally
            {
                if (logger.IsEnabled(LogLevel.Information))
                {
                    TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));

                    // Capturing the duration in seconds as per OpenTelemetry convention for instrument units:
                    // More information here: https://opentelemetry.io/docs/specs/semconv/general/metrics/#instrument-units
                    logger.LogInformation("Function completed. Duration: {Duration}s", duration.TotalSeconds);
                }
            }
        }

        private void ProcessFunctionResult(FunctionResult functionResult)
        {
            string? result = functionResult.GetValue<string>();
            object? usage = functionResult.Metadata?["Usage"];

            if (!string.IsNullOrWhiteSpace(result))
            {
                logger.LogTrace("Function result: {Result}", result);
            }

            if (logger.IsEnabled(LogLevel.Information) && usage is not null)
            {
                logger.LogInformation("Usage: {Usage}", JsonSerializer.Serialize(usage));
            }
        }

        private async IAsyncEnumerable<StreamingChatMessageContent> ProcessFunctionResultStreamingAsync(IAsyncEnumerable<StreamingChatMessageContent> data)
        {
            object? usage = null;

            var stringBuilder = new StringBuilder();

            await foreach (var item in data)
            {
                yield return item;

                if (item.Content is not null)
                {
                    stringBuilder.Append(item.Content);
                }

                usage = item.Metadata?["Usage"];
            }

            var result = stringBuilder.ToString();

            if (!string.IsNullOrWhiteSpace(result))
            {
                logger.LogTrace("Function result: {Result}", result);
            }

            if (logger.IsEnabled(LogLevel.Information) && usage is not null)
            {
                logger.LogInformation("Usage: {Usage}", JsonSerializer.Serialize(usage));
            }
        }
    }

    /// <summary>
    /// Filter which logs an information available during prompt rendering such as rendered prompt.
    /// </summary>
    private sealed class PromptRenderLoggingFilter(ILogger logger) : IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            logger.LogTrace("Rendered prompt: {Prompt}", context.RenderedPrompt);
        }
    }

    /// <summary>
    /// Filter which logs an information available during automatic function calling such as:
    /// Chat history, number of functions to call, which functions to call and their arguments.
    /// </summary>
    private sealed class AutoFunctionInvocationLoggingFilter(ILogger logger) : IAutoFunctionInvocationFilter
    {
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("ChatHistory: {ChatHistory}", JsonSerializer.Serialize(context.ChatHistory));
            }

            if (logger.IsEnabled(LogLevel.Debug))
            {
                logger.LogDebug("Function count: {FunctionCount}", context.FunctionCount);
            }

            var functionCalls = FunctionCallContent.GetFunctionCalls(context.ChatHistory.Last()).ToList();

            if (logger.IsEnabled(LogLevel.Trace))
            {
                functionCalls.ForEach(functionCall
                    => logger.LogTrace(
                        "Function call requests: {PluginName}-{FunctionName}({Arguments})",
                        functionCall.PluginName,
                        functionCall.FunctionName,
                        JsonSerializer.Serialize(functionCall.Arguments)));
            }

            await next(context);
        }
    }
}
