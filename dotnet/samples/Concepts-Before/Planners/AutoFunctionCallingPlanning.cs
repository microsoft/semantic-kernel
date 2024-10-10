// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Planning;

namespace Planners;

/// <summary>
/// This example shows how to implement plan generation and execution with Auto Function Calling and
/// enable telemetry, filters and caching.
/// <see cref="ChatHistory"/> object is used for plan manipulation and execution.
/// </summary>
public class AutoFunctionCallingPlanning(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>Test goal which is used in all examples in this file for comparison purposes.</summary>
    private const string Goal = "Check current UTC time and return current weather in Boston city.";

    /// <summary>JSON serialization configuration for readable output.</summary>
    private readonly JsonSerializerOptions _jsonSerializerOptions = new() { WriteIndented = true };

    /// <summary>
    /// This method contains side by side comparison of Auto Function Calling with FunctionCallingStepwisePlanner.
    /// Both approaches allow to generate and execute a plan by using <see cref="ChatHistory"/> object.
    /// </summary>
    [Fact]
    public async Task SideBySideComparisonWithStepwisePlannerAsync()
    {
        var kernel = GetKernel();

        // 1.1 Plan execution using FunctionCallingStepwisePlanner.
        var planner = new FunctionCallingStepwisePlanner();
        var plannerResult = await planner.ExecuteAsync(kernel, Goal);

        Console.WriteLine($"Planner execution result: {plannerResult.FinalAnswer}");
        Console.WriteLine($"Chat history containing the planning process: {JsonSerializer.Serialize(plannerResult.ChatHistory, _jsonSerializerOptions)}");
        Console.WriteLine($"Planner execution tokens: {GetChatHistoryTokens(plannerResult.ChatHistory)}");

        // Output:
        // Planner execution result: The current UTC time is Sat, 06 Jul 2024 02:11:10 GMT and the weather in Boston is 61 and rainy.
        // Planner execution tokens: 1380

        // 1.2 Plan execution using Auto Function Calling.
        var functionCallingChatHistory = new ChatHistory();
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        functionCallingChatHistory.AddUserMessage(Goal);

        var functionCallingResult = await chatCompletionService.GetChatMessageContentAsync(functionCallingChatHistory, executionSettings, kernel);

        Console.WriteLine($"Auto Function Calling execution result: {functionCallingResult.Content}");
        Console.WriteLine($"Chat history containing the planning process: {JsonSerializer.Serialize(functionCallingChatHistory, _jsonSerializerOptions)}");
        Console.WriteLine($"Auto Function Calling execution tokens: {GetChatHistoryTokens(functionCallingChatHistory)}");

        // Output:
        // Auto Function Calling execution result: The current UTC time is Sat, 06 Jul 2024 02:11:16 GMT.The weather right now in Boston is 61 degrees and rainy.
        // Auto Function Calling execution tokens: 243

        // 2.1 Plan re-execution using FunctionCallingStepwisePlanner.
        // ChatHistory (plan) should be passed without 2 last messages from previously generated ChatHistory.
        plannerResult = await planner.ExecuteAsync(kernel, Goal, new ChatHistory(plannerResult.ChatHistory!.Take(..^2)));
        Console.WriteLine($"Planner re-execution result: {plannerResult.FinalAnswer}");

        // 2.2. Plan re-execution using Auto Function Calling.
        functionCallingResult = await chatCompletionService.GetChatMessageContentAsync(functionCallingChatHistory, executionSettings, kernel);
        Console.WriteLine($"Auto Function Calling re-execution result: {functionCallingResult.Content}");
    }

    /// <summary>
    /// This method shows different plan execution options.
    /// If generated plan is not important and only result is needed - it's possible to use <see cref="Kernel"/> object directly to generate and execute a plan.
    /// If generated plan is important, then an access to <see cref="ChatHistory"/> is required. It's possible to get it by using <see cref="IChatCompletionService"/>.
    /// </summary>
    [Fact]
    public async Task PlanExecutionOptionsAsync()
    {
        var kernel = GetKernel();

        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // If result is the only thing that is needed without generated plan, it's possible to create and execute a plan using Kernel object.
        var kernelResult = await kernel.InvokePromptAsync(Goal, new(executionSettings));

        Console.WriteLine($"Kernel result: {kernelResult}");
        // Output: Kernel result: The current UTC time is Tue, 02 Jul 2024 01:15:28 GMT. The weather in Boston city is 61 degrees and rainy.

        // If result is needed together with generated plan, chat completion service should be used to get an access to the chat history object (generated plan).
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();
        var chatHistory = new ChatHistory();

        chatHistory.AddUserMessage(Goal);

        var chatCompletionServiceResult = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine($"Chat completion service result: {chatCompletionServiceResult.Content}");
        Console.WriteLine($"Chat history containing the planning process: {JsonSerializer.Serialize(chatHistory, _jsonSerializerOptions)}");
        // Output: Chat completion service result: The current UTC time is Tue, 02 Jul 2024 01:15:32 GMT. The weather in Boston city is 61 degrees and rainy.
    }

    /// <summary>
    /// This method shows the telemetry which is produced when using Auto Function Calling to generate and execute a plan.
    /// The example contains produced logs, but metering and tracing are also supported.
    /// More information here: https://github.com/microsoft/semantic-kernel/blob/main/dotnet/docs/TELEMETRY.md.
    /// </summary>
    [Fact]
    public async Task TelemetryForPlanGenerationAndExecutionAsync()
    {
        var kernel = GetKernel(enableLogging: true);

        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var result = await kernel.InvokePromptAsync(Goal, new(executionSettings));

        Console.WriteLine($"Kernel result: {result}");

        // Output:
        // Function InvokePromptAsync_Id invoking.
        // Function arguments: {}
        // Rendered prompt: Check current UTC time and return current weather in Boston city.
        // ChatHistory: [{"Role":{"Label":"user"...
        // Prompt tokens: 86. Completion tokens: 11. Total tokens: 97.
        // Tool requests: 1
        // Function call requests: HelperFunctions-GetCurrentUtcTime({})
        // Function GetCurrentUtcTime invoking.
        // Function arguments: {}
        // Function GetCurrentUtcTime succeeded.
        // Function result: Tue, 02 Jul 2024 01:20:07 GMT
        // Function completed. Duration: 0.0015557s
        // Prompt tokens: 124. Completion tokens: 21. Total tokens: 145.
        // Tool requests: 1
        // Function call requests: HelperFunctions-GetWeatherForCity({"cityName": "Boston"})
        // Function GetWeatherForCity invoking.
        // Function arguments: {"cityName":"Boston"}
        // Function GetWeatherForCity succeeded.
        // Function result: 61 and rainy
        // Function completed. Duration: 0.0019822s
        // Prompt tokens: 161. Completion tokens: 34. Total tokens: 195.
        // Function InvokePromptAsync_Id succeeded.
        // Function result: The current time in UTC is Tue, 02 Jul 2024 01:20:07 GMT. The weather in Boston is 61 degrees and rainy.
        // Function completed. Duration: 5.1014667s
        // Kernel result: The current time in UTC is Tue, 02 Jul 2024 01:20:07 GMT. The weather in Boston is 61 degrees and rainy.
    }

    /// <summary>
    /// This method shows how to cache <see cref="ChatHistory"/> object (generated plan) in order to re-use it later for the same goal.
    /// <see cref="CachedChatCompletionService"/> is used as a caching decorator, which is backed by in-memory cache for demonstration purposes.
    /// </summary>
    [Fact]
    public async Task PlanCachingForReusabilityAsync()
    {
        var kernel = GetKernel();
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Wrap chat completion service from Kernel in caching decorator.
        var chatCompletionService = new CachedChatCompletionService(kernel.GetRequiredService<IChatCompletionService>());

        Console.WriteLine("First run:");

        var firstChatHistory = new ChatHistory([new ChatMessageContent(AuthorRole.User, Goal)]);
        var chatCompletionServiceResult = await ExecuteWithStopwatchAsync(()
            => chatCompletionService.GetChatMessageContentAsync(firstChatHistory, executionSettings, kernel));

        Console.WriteLine($"Plan execution result: {chatCompletionServiceResult.Content}");

        Console.WriteLine("Second run:");

        // New chat history is used without responses from previous run to demonstrate that previous chat history is stored in cache
        // and can be accessed by the same goal.
        var secondChatHistory = new ChatHistory([new ChatMessageContent(AuthorRole.User, Goal)]);
        chatCompletionServiceResult = await ExecuteWithStopwatchAsync(()
            => chatCompletionService.GetChatMessageContentAsync(secondChatHistory, executionSettings, kernel));

        Console.WriteLine($"Plan execution result: {chatCompletionServiceResult.Content}");

        // Output:
        // First run:
        // Elapsed Time: 00:00:04.211
        // Plan execution result: The current UTC time is Tue, 02 Jul 2024 02:23:08 GMT and the weather in Boston is 61 degrees and rainy.
        // Second run:
        // Elapsed Time: 00:00:01.615
        // Plan execution result: The current UTC time is Tue, 02 Jul 2024 02:23:08 GMT and the current weather in Boston is 61°F and rainy.
    }

    /// <summary>
    /// This method shows how to get more control over plan execution using Filters.
    /// <see cref="PlanExecutionFilter"/> is used to override the result of specific plan step (function).
    /// </summary>
    [Fact]
    public async Task UsingFiltersToControlPlanExecutionAsync()
    {
        var kernel = GetKernel();

        kernel.FunctionInvocationFilters.Add(new PlanExecutionFilter());

        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        var result = await kernel.InvokePromptAsync(Goal, new(executionSettings));

        Console.WriteLine($"Kernel result: {result}");
        // Output: Kernel result: The current UTC time is Tue, 02 Jul 2024 01:38:18 GMT and the current weather in Boston city is 70 and sunny.
    }

    /// <summary>
    /// Filter to control plan execution and each step (function).
    /// With filters it's possible to observe which step is going to be executed and its arguments, handle exceptions, override step result.
    /// </summary>
    private sealed class PlanExecutionFilter : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            await next(context);

            // For GetWeatherForCity step, when cityName argument is Boston - return "70 and sunny" result.
            if (context.Function.Name.Equals(nameof(WeatherPlugin.GetWeatherForCity), StringComparison.OrdinalIgnoreCase) &&
                context.Arguments.TryGetValue("cityName", out object? cityName) &&
                cityName!.ToString()!.Equals("Boston", StringComparison.OrdinalIgnoreCase))
            {
                // Override step result.
                context.Result = new FunctionResult(context.Result, "70 and sunny");
            }
        }
    }

    /// <summary>
    /// Caching decorator to re-use previously generated plan and execute it.
    /// This allows to skip plan generation process for the same goal.
    /// </summary>
    private sealed class CachedChatCompletionService(IChatCompletionService innerChatCompletionService) : IChatCompletionService
    {
        /// <summary>In-memory cache for demonstration purposes.</summary>
        private readonly ConcurrentDictionary<string, string> _inMemoryCache = new();

        public IReadOnlyDictionary<string, object?> Attributes => innerChatCompletionService.Attributes;

        public async Task<IReadOnlyList<ChatMessageContent>> GetChatMessageContentsAsync(
            ChatHistory chatHistory,
            PromptExecutionSettings? executionSettings = null,
            Kernel? kernel = null,
            CancellationToken cancellationToken = default)
        {
            // Generate cache key.
            var key = GetCacheKey(chatHistory);

            // Get chat history from cache or use original one.
            var chatHistoryToUse = this._inMemoryCache.TryGetValue(key, out string? cachedChatHistory) ?
                JsonSerializer.Deserialize<ChatHistory>(cachedChatHistory) :
                chatHistory;

            // Execute a request.
            var result = await innerChatCompletionService.GetChatMessageContentsAsync(chatHistoryToUse!, executionSettings, kernel, cancellationToken);

            // Store generated chat history in cache for future usage.
            this._inMemoryCache[key] = JsonSerializer.Serialize(chatHistoryToUse);

            return result;
        }

        public async IAsyncEnumerable<StreamingChatMessageContent> GetStreamingChatMessageContentsAsync(
            ChatHistory chatHistory,
            PromptExecutionSettings? executionSettings = null,
            Kernel? kernel = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await foreach (var item in innerChatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, executionSettings, kernel, cancellationToken))
            {
                yield return item;
            }
        }

        /// <summary>
        /// Hashing is used for a cache key generation for demonstration purposes.
        /// Cache key generation should be implemented based on specific scenario and requirements.
        /// </summary>
        private static string GetCacheKey(ChatHistory chatHistory)
        {
            var goal = chatHistory.First(l => l.Role == AuthorRole.User).Content!;

            byte[] bytes = SHA256.HashData(Encoding.UTF8.GetBytes(goal));

            return BitConverter.ToString(bytes).Replace("-", "").ToUpperInvariant();
        }
    }

    #region Helper methods

    private Kernel GetKernel(bool enableLogging = false)
    {
        var builder = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey);

        if (enableLogging)
        {
            builder.Services.AddSingleton<ILoggerFactory>(this.LoggerFactory);
        }

        var kernel = builder.Build();

        // Import sample plugins.
        kernel.ImportPluginFromType<TimePlugin>();
        kernel.ImportPluginFromType<WeatherPlugin>();

        return kernel;
    }

    private int GetChatHistoryTokens(ChatHistory? chatHistory)
    {
        var tokens = 0;

        if (chatHistory is null)
        {
            return tokens;
        }

        foreach (var message in chatHistory)
        {
            if (message.Metadata is not null &&
                message.Metadata.TryGetValue("Usage", out object? usage) &&
                usage is CompletionsUsage completionsUsage &&
                completionsUsage is not null)
            {
                tokens += completionsUsage.TotalTokens;
            }
        }

        return tokens;
    }

    private async Task<ChatMessageContent> ExecuteWithStopwatchAsync(Func<Task<ChatMessageContent>> action)
    {
        var stopwatch = Stopwatch.StartNew();

        var result = await action();

        stopwatch.Stop();

        Console.WriteLine($@"Elapsed Time: {stopwatch.Elapsed:hh\:mm\:ss\.FFF}");

        return result;
    }

    #endregion

    #region Sample plugins

    private sealed class TimePlugin
    {
        [KernelFunction]
        [Description("Retrieves the current time in UTC")]
        public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction]
        [Description("Gets the current weather for the specified city")]
        public string GetWeatherForCity(string cityName) =>
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
            };
    }

    #endregion
}
