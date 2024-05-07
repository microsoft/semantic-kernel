// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Memory;

namespace Caching;

public class SemanticCachingWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    private const double SimilarityScore = 0.9;

    [Fact]
    public async Task InMemoryCacheAsync()
    {
        var kernel = GetKernelWithCache(_ => new VolatileMemoryStore());

        var result1 = await ExecuteAsync(kernel, "First run", "What's the tallest building in New York?");
        var result2 = await ExecuteAsync(kernel, "Second run", "What is the highest building in New York City?");

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");
    }

    [Fact]
    public async Task RedisCacheAsync()
    {
        var kernel = GetKernelWithCache(_ => new RedisMemoryStore("localhost:6379", vectorSize: 1536));

        var result1 = await ExecuteAsync(kernel, "First run", "What's the tallest building in New York?");
        var result2 = await ExecuteAsync(kernel, "Second run", "What is the highest building in New York City?");

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");
    }

    [Fact]
    public async Task AzureCosmosDBMongoDBCacheAsync()
    {
        var kernel = GetKernelWithCache(_ => new AzureCosmosDBMongoDBMemoryStore(
            TestConfiguration.AzureCosmosDbMongoDb.ConnectionString,
            TestConfiguration.AzureCosmosDbMongoDb.DatabaseName,
            new()
            {
                Kind = AzureCosmosDBVectorSearchType.VectorIVF,
                Similarity = AzureCosmosDBSimilarityType.Cosine,
                Dimensions = 1536
            }));

        var result1 = await ExecuteAsync(kernel, "First run", "What's the tallest building in New York?");
        var result2 = await ExecuteAsync(kernel, "Second run", "What is the highest building in New York City?");

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");
    }

    #region Configuration

    private Kernel GetKernelWithCache(Func<IServiceProvider, IMemoryStore> cacheFactory)
    {
        var builder = Kernel.CreateBuilder();

        builder.AddAzureOpenAIChatCompletion(
            TestConfiguration.AzureOpenAI.ChatDeploymentName,
            TestConfiguration.AzureOpenAI.Endpoint,
            TestConfiguration.AzureOpenAI.ApiKey);

        builder.AddAzureOpenAITextEmbeddingGeneration(
            TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            TestConfiguration.AzureOpenAIEmbeddings.ApiKey);

        builder.Services.AddSingleton<IMemoryStore>(cacheFactory);
        builder.Services.AddSingleton<ISemanticTextMemory, SemanticTextMemory>();

        builder.Services.AddSingleton<IFunctionInvocationFilter, FunctionCacheFilter>();
        builder.Services.AddSingleton<IPromptRenderFilter>(
            (sp) => new PromptCacheFilter(sp.GetRequiredService<ISemanticTextMemory>(), SimilarityScore));

        return builder.Build();
    }

    #endregion

    #region Caching filters

    public class CacheBaseFilter
    {
        protected const string CacheCollectionName = "llm_responses";

        protected const string CacheRecordIdKey = "CacheRecordId";
    }

    public sealed class PromptCacheFilter(ISemanticTextMemory semanticTextMemory, double minRelevanceScore) : CacheBaseFilter, IPromptRenderFilter
    {
        public async Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            await next(context);

            var prompt = context.RenderedPrompt!;

            var searchResult = await semanticTextMemory.SearchAsync(
                CacheCollectionName,
                prompt,
                limit: 1,
                minRelevanceScore: minRelevanceScore).FirstOrDefaultAsync();

            if (searchResult is not null)
            {
                context.Result = new FunctionResult(context.Function, searchResult.Metadata.AdditionalMetadata)
                {
                    Metadata = new Dictionary<string, object?> { [CacheRecordIdKey] = searchResult.Metadata.Id }
                };
            }
        }
    }

    public sealed class FunctionCacheFilter(ISemanticTextMemory semanticTextMemory) : CacheBaseFilter, IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            await next(context);

            var result = context.Result;

            if (!string.IsNullOrEmpty(context.Result.RenderedPrompt))
            {
                var recordId = context.Result.Metadata?.GetValueOrDefault(CacheRecordIdKey, Guid.NewGuid().ToString()) as string;

                await semanticTextMemory.SaveInformationAsync(
                    CacheCollectionName,
                    context.Result.RenderedPrompt,
                    recordId!,
                    additionalMetadata: result.ToString(),
                    timestamp: DateTimeOffset.UtcNow);
            }
        }
    }

    #endregion

    #region Execution

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
