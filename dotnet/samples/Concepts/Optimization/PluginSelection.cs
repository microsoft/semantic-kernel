// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Optimization;

/// <summary>
/// Single kernel instance may have multiple imported plugins/functions. It's possible to enable automatic function calling,
/// so AI model will decide which functions to call for specific request.
/// In case there are a lot of plugins/functions in application, some of them (or all of them) need to be shared with the model.
/// This example shows how to use different plugin/function selection strategies, to share with AI only those functions,
/// which are related to specific request.
/// This technique should decrease token usage, as fewer functions will be shared with AI.
/// </summary>
public sealed class PluginSelection(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This method shows how to select best function to share with AI using vector similarity search.
    /// </summary>
    [Fact]
    public async Task UsingVectorSearchAsync()
    {
        // Initialize kernel with chat completion and embedding generation services.
        // It's possible to combine different models from different AI providers to achieve the lowest token usage.
        var builder = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey)
            .AddOpenAITextEmbeddingGeneration("text-embedding-3-small", TestConfiguration.OpenAI.ApiKey);

        // Add logging.
        var logger = this.LoggerFactory.CreateLogger<PluginSelection>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add memory store to keep functions and search for the most relevant ones for specific request.
        builder.Services.AddSingleton<IMemoryStore, VolatileMemoryStore>();

        var kernel = builder.Build();

        // Import plugins with different features.
        kernel.ImportPluginFromType<TimePlugin>();
        kernel.ImportPluginFromType<WeatherPlugin>();
        kernel.ImportPluginFromType<EmailPlugin>();
        kernel.ImportPluginFromType<NewsPlugin>();
        kernel.ImportPluginFromType<CalendarPlugin>();

        // Enable automatic function calling.
        var executionSettings = new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

        // Define kernel arguments with specific request.
        var kernelArguments = new KernelArguments(executionSettings) { ["Request"] = "Provide latest headlines" };

        // Invoke the request without plugin selection filter first for comparison purposes.
        Console.WriteLine("Run without filter:");
        var result = await kernel.InvokePromptAsync("{{$Request}}", kernelArguments);

        Console.WriteLine(result);
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Total tokens: ~250

        // Define plugin selection filter.
        var filter = new PluginSelectionFilter(
            kernel.GetRequiredService<IMemoryStore>(),
            kernel.GetRequiredService<ITextEmbeddingGenerationService>(),
            kernel.GetRequiredService<ILogger>());

        // Add filter to kernel.
        kernel.FunctionInvocationFilters.Add(filter);

        // Invoke the request with plugin selection filter.
        Console.WriteLine("\nRun with filter:");
        result = await kernel.InvokePromptAsync("{{$Request}}", kernelArguments);

        Console.WriteLine(result);
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Total tokens: ~150
    }

    /// <summary>
    /// Filter which performs vector similarity search on imported functions in <see cref="Kernel"/>
    /// to select the best one to share with AI.
    /// </summary>
    private sealed class PluginSelectionFilter(
        IMemoryStore memoryStore,
        ITextEmbeddingGenerationService textEmbeddingGenerationService,
        ILogger logger) : IFunctionInvocationFilter
    {
        /// <summary>Collection name to use in memory store.</summary>
        private const string CollectionName = "functions";

        /// <summary>Number of best functions to share with AI.</summary>
        private const int NumberOfBestFunctions = 1;

        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            var request = GetRequestArgument(context.Arguments);

            // Execute plugin selection logic for "InvokePrompt" function only, as main entry point.
            if (context.Function.Name.Contains(nameof(KernelExtensions.InvokePromptAsync)) && !string.IsNullOrWhiteSpace(request))
            {
                // Get imported plugins in kernel.
                var plugins = context.Kernel.Plugins;

                // Store plugins in memory store.
                await this.StorePluginsAsync(plugins);

                // Find best functions for original request.
                var bestFunctions = await this.GetBestFunctionsAsync(plugins, request);

                // If any found, update execution settings and execute the request.
                if (bestFunctions.Count > 0)
                {
                    bestFunctions.ForEach(function
                        => logger.LogInformation("Best function found: {PluginName}-{FunctionName}", function.PluginName, function.Name));

                    var updatedExecutionSettings = GetExecutionSettings(context.Arguments, bestFunctions);

                    if (updatedExecutionSettings is not null)
                    {
                        context.Arguments.ExecutionSettings = updatedExecutionSettings;

                        await next(context);

                        return;
                    }
                }
            }

            // Otherwise, execute a request with default logic, where all plugins will be shared.
            await next(context);
        }

        private async Task StorePluginsAsync(KernelPluginCollection plugins)
        {
            // Collect data about imported functions in kernel.
            var memoryRecords = new List<MemoryRecord>();
            var functionsData = GetFunctionsData(plugins);

            // Generate embedding for each function.
            var embeddings = await textEmbeddingGenerationService
                .GenerateEmbeddingsAsync(functionsData.Select(l => l.TextToVectorize).ToArray());

            // Create memory record instances with function information and embedding.
            for (var i = 0; i < functionsData.Count; i++)
            {
                var (function, textToVectorize) = functionsData[i];

                memoryRecords.Add(MemoryRecord.LocalRecord(
                    id: GetFunctionKey(function.Name, function.PluginName),
                    text: textToVectorize,
                    description: null,
                    embedding: embeddings[i]));
            }

            // Create collection and upsert all memory records for search.
            // It's possible to do it only once and re-use the same functions for future requests.
            await memoryStore.CreateCollectionAsync(CollectionName);
            await memoryStore.UpsertBatchAsync(CollectionName, memoryRecords).ToListAsync();
        }

        private async Task<List<KernelFunction>> GetBestFunctionsAsync(KernelPluginCollection plugins, string request)
        {
            // Generate embedding for original request.
            var requestEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(request);

            // Find best functions to call for original request.
            var memoryRecordKeys = await memoryStore
                .GetNearestMatchesAsync(CollectionName, requestEmbedding, limit: NumberOfBestFunctions)
                .Select(l => l.Item1.Key)
                .ToListAsync();

            return plugins
                .SelectMany(plugin => plugin)
                .Where(function => memoryRecordKeys.Contains(GetFunctionKey(function.Name, function.PluginName)))
                .ToList();
        }

        private static string GetFunctionKey(string functionName, string? pluginName)
            => !string.IsNullOrWhiteSpace(pluginName) ? $"{pluginName}-{functionName}" : functionName;

        private static string? GetRequestArgument(KernelArguments arguments)
            => arguments.TryGetValue("Request", out var requestObj) && requestObj is string request ? request : null;

        private static List<(KernelFunction Function, string TextToVectorize)> GetFunctionsData(KernelPluginCollection plugins)
            => plugins
                .SelectMany(plugin => plugin)
                .Select(function => (function, $"Plugin name: {function.PluginName}. Function name: {function.Name}. Description: {function.Description}"))
                .ToList();

        private static Dictionary<string, PromptExecutionSettings>? GetExecutionSettings(KernelArguments arguments, List<KernelFunction> functions)
        {
            var promptExecutionSettings = arguments.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId];

            if (promptExecutionSettings is not null && promptExecutionSettings is OpenAIPromptExecutionSettings openAIPromptExecutionSettings)
            {
                var openAIFunctions = functions.Select(function => function.Metadata.ToOpenAIFunction());
                openAIPromptExecutionSettings.ToolCallBehavior = ToolCallBehavior.EnableFunctions(openAIFunctions, autoInvoke: true);

                return new() { [PromptExecutionSettings.DefaultServiceId] = openAIPromptExecutionSettings };
            }

            return null;
        }
    }

    #region Sample Plugins

    private sealed class TimePlugin
    {
        [KernelFunction, Description("Provides the current date and time.")]
        public string GetCurrentTime() => DateTime.Now.ToString("R");
    }

    private sealed class WeatherPlugin
    {
        [KernelFunction, Description("Provides weather information for various cities.")]
        public string GetWeather(string cityName) => cityName switch
        {
            "Boston" => "61 and rainy",
            "London" => "55 and cloudy",
            "Miami" => "80 and sunny",
            "Paris" => "60 and rainy",
            "Tokyo" => "50 and sunny",
            "Sydney" => "75 and sunny",
            "Tel Aviv" => "80 and sunny",
            _ => "No information",
        };
    }

    private sealed class EmailPlugin(ILogger logger)
    {
        [KernelFunction, Description("Sends email to recipient with subject and body.")]
        public void SendEmail(string from, string to, string subject, string body)
        {
            logger.LogInformation("Email has been sent successfully.");
        }
    }

    private sealed class NewsPlugin
    {
        [KernelFunction, Description("Provides the latest news headlines.")]
        public List<string> GetLatestHeadlines() => new()
        {
            "Tourism Industry Sees Record Growth",
            "Tech Company Releases New Product",
            "Sports Team Wins Championship",
            "New Study Reveals Health Benefits of Walking"
        };
    }

    private sealed class CalendarPlugin
    {
        [KernelFunction, Description("Provides a list of upcoming events.")]
        public List<string> GetUpcomingEvents() => new()
        {
            "Meeting with Bob on June 22",
            "Project deadline on June 30",
            "Dentist appointment on July 5",
            "Vacation starts on July 12"
        };
    }

    #endregion
}
