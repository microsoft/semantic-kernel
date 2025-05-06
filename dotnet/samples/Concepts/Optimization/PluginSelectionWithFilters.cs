// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel.Embeddings;

namespace Optimization;

/// <summary>
/// Single kernel instance may have multiple imported plugins/functions. It's possible to enable automatic function calling,
/// so AI model will decide which functions to call for specific request.
/// In case there are a lot of plugins/functions in application, some of them (or all of them) need to be shared with the model.
/// This example shows how to use different plugin/function selection strategies, to share with AI only those functions,
/// which are related to specific request.
/// This technique should decrease token usage, as fewer functions will be shared with AI.
/// It also helps to handle the scenario with a general purpose chat experience for a large enterprise,
/// where there are so many plugins, that it's impossible to share all of them with AI model in a single request.
/// </summary>
public sealed class PluginSelectionWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This method shows how to select best functions to share with AI using vector similarity search.
    /// </summary>
    [Fact]
    public async Task UsingVectorSearchWithKernelAsync()
    {
        // Initialize kernel with chat completion and embedding generation services.
        // It's possible to combine different models from different AI providers to achieve the lowest token usage.
        var builder = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey)
            .AddOpenAITextEmbeddingGeneration("text-embedding-3-small", TestConfiguration.OpenAI.ApiKey);

        // Add logging.
        var logger = this.LoggerFactory.CreateLogger<PluginSelectionWithFilters>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add vector store to keep functions and search for the most relevant ones for specific request.
        builder.Services.AddInMemoryVectorStore();

        // Add helper components defined in this example.
        builder.Services.AddSingleton<IFunctionProvider, FunctionProvider>();
        builder.Services.AddSingleton<IFunctionKeyProvider, FunctionKeyProvider>();
        builder.Services.AddSingleton<IPluginStore, PluginStore>();

        var kernel = builder.Build();

        // Import plugins with different features.
        kernel.ImportPluginFromType<TimePlugin>();
        kernel.ImportPluginFromType<WeatherPlugin>();
        kernel.ImportPluginFromType<EmailPlugin>();
        kernel.ImportPluginFromType<NewsPlugin>();
        kernel.ImportPluginFromType<CalendarPlugin>();

        // Get registered plugin store to save information about plugins.
        var pluginStore = kernel.GetRequiredService<IPluginStore>();

        // Save information about kernel plugins in plugin store.
        const string CollectionName = "functions";

        await pluginStore.SaveAsync(CollectionName, kernel.Plugins);

        // Enable automatic function calling by default.
        var executionSettings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Define kernel arguments with specific request.
        var kernelArguments = new KernelArguments(executionSettings) { ["Request"] = "Provide latest headlines" };

        // Invoke the request without plugin selection filter first for comparison purposes.
        Console.WriteLine("Run without filter:");
        var result = await kernel.InvokePromptAsync("{{$Request}}", kernelArguments);

        Console.WriteLine(result);
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // All functions were shared with AI. Total tokens: ~250

        // Define plugin selection filter.
        var filter = new PluginSelectionFilter(
            functionProvider: kernel.GetRequiredService<IFunctionProvider>(),
            logger: kernel.GetRequiredService<ILogger>(),
            collectionName: CollectionName,
            numberOfBestFunctions: 1);

        // Add filter to kernel.
        kernel.FunctionInvocationFilters.Add(filter);

        // Invoke the request with plugin selection filter.
        Console.WriteLine("\nRun with filter:");

        // FunctionChoiceBehavior.Auto() is used here as well as defined above.
        // In case there will be related functions found for specific request, the FunctionChoiceBehavior will be updated in filter to
        // FunctionChoiceBehavior.Auto(functions) - this will allow to share only related set of functions with AI.
        result = await kernel.InvokePromptAsync("{{$Request}}", kernelArguments);

        Console.WriteLine(result);
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Just one function was shared with AI. Total tokens: ~150
    }

    [Fact]
    public async Task UsingVectorSearchWithChatCompletionAsync()
    {
        // Initialize kernel with chat completion and embedding generation services.
        // It's possible to combine different models from different AI providers to achieve the lowest token usage.
        var builder = Kernel
            .CreateBuilder()
            .AddOpenAIChatCompletion("gpt-4", TestConfiguration.OpenAI.ApiKey)
            .AddOpenAITextEmbeddingGeneration("text-embedding-3-small", TestConfiguration.OpenAI.ApiKey);

        // Add logging.
        var logger = this.LoggerFactory.CreateLogger<PluginSelectionWithFilters>();
        builder.Services.AddSingleton<ILogger>(logger);

        // Add vector store to keep functions and search for the most relevant ones for specific request.
        builder.Services.AddInMemoryVectorStore();

        // Add helper components defined in this example.
        builder.Services.AddSingleton<IFunctionProvider, FunctionProvider>();
        builder.Services.AddSingleton<IFunctionKeyProvider, FunctionKeyProvider>();
        builder.Services.AddSingleton<IPluginStore, PluginStore>();

        var kernel = builder.Build();

        // Import plugins with different features.
        kernel.ImportPluginFromType<TimePlugin>();
        kernel.ImportPluginFromType<WeatherPlugin>();
        kernel.ImportPluginFromType<EmailPlugin>();
        kernel.ImportPluginFromType<NewsPlugin>();
        kernel.ImportPluginFromType<CalendarPlugin>();

        // Get registered plugin store to save information about plugins.
        var pluginStore = kernel.GetRequiredService<IPluginStore>();

        // Store information about kernel plugins in plugin store.
        const string CollectionName = "functions";

        await pluginStore.SaveAsync(CollectionName, kernel.Plugins);

        // Enable automatic function calling by default.
        var executionSettings = new OpenAIPromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() };

        // Get function provider and find best functions for specified prompt.
        var functionProvider = kernel.GetRequiredService<IFunctionProvider>();

        const string Prompt = "Provide latest headlines";

        var bestFunctions = await functionProvider.GetBestFunctionsAsync(CollectionName, Prompt, kernel.Plugins, numberOfBestFunctions: 1);

        // If any found, update execution settings to share only selected functions.
        if (bestFunctions.Count > 0)
        {
            bestFunctions.ForEach(function
                => logger.LogInformation("Best function found: {PluginName}-{FunctionName}", function.PluginName, function.Name));

            // Share only selected functions with AI.
            executionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(bestFunctions);
        }

        // Get chat completion service and execute a request.
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage(Prompt);

        var result = await chatCompletionService.GetChatMessageContentAsync(chatHistory, executionSettings, kernel);

        Console.WriteLine(result);
        Console.WriteLine(result.Metadata?["Usage"]?.AsJson()); // Just one function was shared with AI. Total tokens: ~150
    }

    /// <summary>
    /// Filter which performs vector similarity search on imported functions in <see cref="Kernel"/>
    /// to select the best ones to share with AI.
    /// </summary>
    private sealed class PluginSelectionFilter(
        IFunctionProvider functionProvider,
        ILogger logger,
        string collectionName,
        int numberOfBestFunctions) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            var request = GetRequestArgument(context.Arguments);

            // Execute plugin selection logic for "InvokePrompt" function only, as main entry point.
            if (context.Function.Name.Contains(nameof(KernelExtensions.InvokePromptAsync)) && !string.IsNullOrWhiteSpace(request))
            {
                // Get imported plugins in kernel.
                var plugins = context.Kernel.Plugins;

                // Find best functions for original request.
                var bestFunctions = await functionProvider.GetBestFunctionsAsync(collectionName, request, plugins, numberOfBestFunctions);

                // If any found, update execution settings and execute the request.
                if (bestFunctions.Count > 0)
                {
                    bestFunctions.ForEach(function
                        => logger.LogInformation("Best function found: {PluginName}-{FunctionName}", function.PluginName, function.Name));

                    var updatedExecutionSettings = GetExecutionSettings(context.Arguments, bestFunctions);

                    if (updatedExecutionSettings is not null)
                    {
                        // Update execution settings.
                        context.Arguments.ExecutionSettings = updatedExecutionSettings;

                        // Execute the request.
                        await next(context);

                        return;
                    }
                }
            }

            // Otherwise, execute a request with default logic, where all plugins will be shared.
            await next(context);
        }

        private static Dictionary<string, PromptExecutionSettings>? GetExecutionSettings(KernelArguments arguments, List<KernelFunction> functions)
        {
            var promptExecutionSettings = arguments.ExecutionSettings?[PromptExecutionSettings.DefaultServiceId];

            if (promptExecutionSettings is not null && promptExecutionSettings is OpenAIPromptExecutionSettings openAIPromptExecutionSettings)
            {
                // Share only selected functions with AI.
                openAIPromptExecutionSettings.FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(functions);

                return new() { [PromptExecutionSettings.DefaultServiceId] = openAIPromptExecutionSettings };
            }

            return null;
        }

        private static string? GetRequestArgument(KernelArguments arguments)
            => arguments.TryGetValue("Request", out var requestObj) && requestObj is string request ? request : null;
    }

    #region Helper components

    /// <summary>
    /// Helper function key provider.
    /// </summary>
    public interface IFunctionKeyProvider
    {
        string GetFunctionKey(KernelFunction kernelFunction);
    }

    /// <summary>
    /// Helper function provider to get best functions for specific request.
    /// </summary>
    public interface IFunctionProvider
    {
        Task<List<KernelFunction>> GetBestFunctionsAsync(
            string collectionName,
            string request,
            KernelPluginCollection plugins,
            int numberOfBestFunctions,
            CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Helper plugin store to save information about imported plugins in vector database.
    /// </summary>
    public interface IPluginStore
    {
        Task SaveAsync(string collectionName, KernelPluginCollection plugins, CancellationToken cancellationToken = default);
    }

    public class FunctionKeyProvider : IFunctionKeyProvider
    {
        public string GetFunctionKey(KernelFunction kernelFunction)
        {
            return !string.IsNullOrWhiteSpace(kernelFunction.PluginName) ?
                $"{kernelFunction.PluginName}-{kernelFunction.Name}" :
                kernelFunction.Name;
        }
    }

    public class FunctionProvider(
        ITextEmbeddingGenerationService textEmbeddingGenerationService,
        IVectorStore vectorStore,
        IFunctionKeyProvider functionKeyProvider) : IFunctionProvider
    {
        public async Task<List<KernelFunction>> GetBestFunctionsAsync(
            string collectionName,
            string request,
            KernelPluginCollection plugins,
            int numberOfBestFunctions,
            CancellationToken cancellationToken = default)
        {
            // Generate embedding for original request.
            var requestEmbedding = await textEmbeddingGenerationService.GenerateEmbeddingAsync(request, cancellationToken: cancellationToken);

            var collection = vectorStore.GetCollection<string, FunctionRecord>(collectionName);
            await collection.CreateCollectionIfNotExistsAsync(cancellationToken);

            // Find best functions to call for original request.
            var recordKeys = (await collection.SearchEmbeddingAsync(requestEmbedding, top: numberOfBestFunctions, cancellationToken: cancellationToken)
                .ToListAsync(cancellationToken)).Select(l => l.Record.Id);

            return plugins
                .SelectMany(plugin => plugin)
                .Where(function => recordKeys.Contains(functionKeyProvider.GetFunctionKey(function)))
                .ToList();
        }
    }

    public class PluginStore(
        ITextEmbeddingGenerationService textEmbeddingGenerationService,
        IVectorStore vectorStore,
        IFunctionKeyProvider functionKeyProvider) : IPluginStore
    {
        public async Task SaveAsync(string collectionName, KernelPluginCollection plugins, CancellationToken cancellationToken = default)
        {
            // Collect data about imported functions in kernel.
            var functionRecords = new List<FunctionRecord>();
            var functionsData = GetFunctionsData(plugins);

            // Generate embedding for each function.
            var embeddings = await textEmbeddingGenerationService
                .GenerateEmbeddingsAsync(functionsData.Select(l => l.TextToVectorize).ToArray(), cancellationToken: cancellationToken);

            // Create vector store record instances with function information and embedding.
            for (var i = 0; i < functionsData.Count; i++)
            {
                var (function, functionInfo) = functionsData[i];

                functionRecords.Add(new FunctionRecord
                {
                    Id = functionKeyProvider.GetFunctionKey(function),
                    FunctionInfo = functionInfo,
                    FunctionInfoEmbedding = embeddings[i]
                });
            }

            // Create collection and upsert all vector store records for search.
            // It's possible to do it only once and re-use the same functions for future requests.
            var collection = vectorStore.GetCollection<string, FunctionRecord>(collectionName);
            await collection.CreateCollectionIfNotExistsAsync(cancellationToken);

            await collection.UpsertAsync(functionRecords, cancellationToken: cancellationToken);
        }

        private static List<(KernelFunction Function, string TextToVectorize)> GetFunctionsData(KernelPluginCollection plugins)
            => plugins
                .SelectMany(plugin => plugin)
                .Select(function => (function, $"Plugin name: {function.PluginName}. Function name: {function.Name}. Description: {function.Description}"))
                .ToList();
    }

    #endregion

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

    #region Vector Store Record

    private sealed class FunctionRecord
    {
        [VectorStoreRecordKey]
        public string Id { get; set; }

        [VectorStoreRecordData]
        public string FunctionInfo { get; set; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> FunctionInfoEmbedding { get; set; }
    }

    #endregion
}
