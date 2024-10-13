// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Memory;

namespace Caching;

/// <summary>
/// This example shows how to achieve Semantic Caching with Filters.
/// <see cref="IPromptRenderFilter"/> is used to get rendered prompt and check in cache if similar prompt was already answered.
/// If there is a record in cache, then previously cached answer will be returned to the user instead of making a call to LLM.
/// If there is no record in cache, a call to LLM will be performed, and result will be cached together with rendered prompt.
/// <see cref="IFunctionInvocationFilter"/> is used to update cache with rendered prompt and related LLM result.
/// </summary>
public class SemanticCachingWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Similarity/relevance score, from 0 to 1, where 1 means exact match.
    /// It's possible to change this value during testing to see how caching logic will behave.
    /// </summary>
    private const double SimilarityScore = 0.9;

    /// <summary>
    /// Executing similar requests two times using in-memory caching store to compare execution time and results.
    /// Second execution is faster, because the result is returned from cache.
    /// </summary>
    [Fact]
    public async Task InMemoryCacheAsync()
    {
        var kernel = GetKernelWithCache(_ => new VolatileMemoryStore());

        var result1 = await ExecuteAsync(kernel, "First run", "What's the tallest building in New York?");
        var result2 = await ExecuteAsync(kernel, "Second run", "What is the highest building in New York City?");

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");

        /*
        Output:
        First run: What's the tallest building in New York?
        Elapsed Time: 00:00:03.828
        Second run: What is the highest building in New York City?
        Elapsed Time: 00:00:00.541
        Result 1: The tallest building in New York is One World Trade Center, also known as Freedom Tower.It stands at 1,776 feet(541.3 meters) tall, including its spire.
        Result 2: The tallest building in New York is One World Trade Center, also known as Freedom Tower.It stands at 1,776 feet(541.3 meters) tall, including its spire.
        */
    }

    /// <summary>
    /// Executing similar requests two times using Redis caching store to compare execution time and results.
    /// Second execution is faster, because the result is returned from cache.
    /// How to run Redis on Docker locally: https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/docker/
    /// </summary>
    [Fact]
    public async Task RedisCacheAsync()
    {
        var kernel = GetKernelWithCache(_ => new RedisMemoryStore("localhost:6379", vectorSize: 1536));

        var result1 = await ExecuteAsync(kernel, "First run", "What's the tallest building in New York?");
        var result2 = await ExecuteAsync(kernel, "Second run", "What is the highest building in New York City?");

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");

        /*
        First run: What's the tallest building in New York?
        Elapsed Time: 00:00:03.674
        Second run: What is the highest building in New York City?
        Elapsed Time: 00:00:00.292
        Result 1: The tallest building in New York is One World Trade Center, also known as Freedom Tower. It stands at 1,776 feet (541 meters) tall, including its spire.
        Result 2: The tallest building in New York is One World Trade Center, also known as Freedom Tower. It stands at 1,776 feet (541 meters) tall, including its spire.
        */
    }

    /// <summary>
    /// Executing similar requests two times using Azure Cosmos DB for MongoDB caching store to compare execution time and results.
    /// Second execution is faster, because the result is returned from cache.
    /// How to setup Azure Cosmos DB for MongoDB cluster: https://learn.microsoft.com/en-gb/azure/cosmos-db/mongodb/vcore/quickstart-portal
    /// </summary>
    [Fact]
    public async Task AzureCosmosDBMongoDBCacheAsync()
    {
        var kernel = GetKernelWithCache(_ => new AzureCosmosDBMongoDBMemoryStore(
            TestConfiguration.AzureCosmosDbMongoDb.ConnectionString,
            TestConfiguration.AzureCosmosDbMongoDb.DatabaseName,
            new(dimensions: 1536)));

        var result1 = await ExecuteAsync(kernel, "First run", "What's the tallest building in New York?");
        var result2 = await ExecuteAsync(kernel, "Second run", "What is the highest building in New York City?");

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");

        /*
        First run: What's the tallest building in New York?
        Elapsed Time: 00:00:05.485
        Second run: What is the highest building in New York City?
        Elapsed Time: 00:00:00.389
        Result 1: The tallest building in New York is One World Trade Center, also known as Freedom Tower, which stands at 1,776 feet (541.3 meters) tall.
        Result 2: The tallest building in New York is One World Trade Center, also known as Freedom Tower, which stands at 1,776 feet (541.3 meters) tall.
        */
    }

    #region Configuration

    /// <summary>
    /// Returns <see cref="Kernel"/> instance with required registered services.
    /// </summary>
    private Kernel GetKernelWithCache(Func<IServiceProvider, IMemoryStore> cacheFactory)
    {
        var builder = Kernel.CreateBuilder();

        // Add Azure OpenAI chat completion service
        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        // Add Azure OpenAI text embedding generation service
        builder.AddAzureOpenAITextEmbeddingGeneration(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        // Add memory store for caching purposes (e.g. in-memory, Redis, Azure Cosmos DB)
        builder.Services.AddSingleton<IMemoryStore>(cacheFactory);

        // Add text memory service that will be used to generate embeddings and query/store data. 
        builder.Services.AddSingleton<ISemanticTextMemory, SemanticTextMemory>();

        // Add prompt render filter to query cache and check if rendered prompt was already answered.
        builder.Services.AddSingleton<IPromptRenderFilter, PromptCacheFilter>();

        // Add function invocation filter to cache rendered prompts and LLM results.
        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionCacheFilter>();

        return builder.Build();
    }

    #endregion

    #region Cache Filters

    /// <summary>
    /// Base class for filters that contains common constant values.
    /// </summary>
    public class CacheBaseFilter
    {
        /// <summary>
        /// Collection/table name in cache to use.
        /// </summary>
        protected const string CollectionName = "llm_responses";

        /// <summary>
        /// Metadata key in function result for cache record id, which is used to overwrite previously cached response.
        /// </summary>
        protected const string RecordIdKey = "CacheRecordId";
    }

    /// <summary>
    /// Filter which is executed during prompt rendering operation.
    /// </summary>
    public sealed class PromptCacheFilter(ISemanticTextMemory semanticTextMemory) : CacheBaseFilter, IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            // Trigger prompt rendering operation
            await next(context);

            // Get rendered prompt
            var prompt = context.RenderedPrompt!;

            // Search for similar prompts in cache with provided similarity/relevance score
            var searchResult = await semanticTextMemory.SearchAsync(
                CollectionName,
                prompt,
                limit: 1,
                minRelevanceScore: SimilarityScore).FirstOrDefaultAsync();

            // If result exists, return it.
            if (searchResult is not null)
            {
                // Override function result. This will prevent calling LLM and will return result immediately.
                context.Result = new FunctionResult(context.Function, searchResult.Metadata.AdditionalMetadata)
                {
                    Metadata = new Dictionary<string, object?> { [RecordIdKey] = searchResult.Metadata.Id }
                };
            }
        }
    }

    /// <summary>
    /// Filter which is executed during function invocation.
    /// </summary>
    public sealed class FunctionCacheFilter(ISemanticTextMemory semanticTextMemory) : CacheBaseFilter, IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Trigger function invocation
            await next(context);

            // Get function invocation result
            var result = context.Result;

            // If there was any rendered prompt, cache it together with LLM result for future calls.
            if (!string.IsNullOrEmpty(context.Result.RenderedPrompt))
            {
                // Get cache record id if result was cached previously or generate new id.
                var recordId = context.Result.Metadata?.GetValueOrDefault(RecordIdKey, Guid.NewGuid().ToString()) as string;

                // Cache rendered prompt and LLM result.
                await semanticTextMemory.SaveInformationAsync(
                    CollectionName,
                    context.Result.RenderedPrompt,
                    recordId!,
                    additionalMetadata: result.ToString());
            }
        }
    }

    #endregion

    #region Execution

    /// <summary>
    /// Helper method to invoke prompt and measure execution time for comparison.
    /// </summary>
    private async Task<FunctionResult> ExecuteAsync(Kernel kernel, string title, string prompt)
    {
        Console.WriteLine($"{title}: {prompt}");

        var stopwatch = Stopwatch.StartNew();

        var result = await kernel.InvokePromptAsync(prompt);

        stopwatch.Stop();

        Console.WriteLine($@"Elapsed Time: {stopwatch.Elapsed:hh\:mm\:ss\.FFF}");

        return result;
    }

    #endregion
}
