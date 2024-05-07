// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;

namespace Caching;

public class SemanticCachingWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    private const double SimilarityScore = 0.9;

    [Fact]
    public async Task InMemoryCacheAsync()
    {
        var kernel = GetKernel(_ => new VolatileMemoryStore());

        Console.WriteLine("First run:");
        var result1 = await ExecuteAsync(() => kernel.InvokePromptAsync("What's the tallest building in New York?"));

        Console.WriteLine("Second run:");
        var result2 = await ExecuteAsync(() => kernel.InvokePromptAsync("What is the highest building in New York City?"));

        Console.WriteLine($"Result 1: {result1}");
        Console.WriteLine($"Result 2: {result2}");
    }

    [Fact]
    public async Task RedisCacheAsync()
    {

    }

    [Fact]
    public async Task AzureCosmosDBMongoDBCacheAsync()
    {

    }

    #region Configuration

    private Kernel GetKernel(Func<IServiceProvider, IMemoryStore> cacheFactory)
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

        protected const string IsCachedResultKey = "IsCachedResult";
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
                    Metadata = new Dictionary<string, object?> { [IsCachedResultKey] = true }
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
                await semanticTextMemory.SaveInformationAsync(
                    CacheCollectionName,
                    context.Result.RenderedPrompt,
                    Guid.NewGuid().ToString(),
                    additionalMetadata: result.ToString());
            }
        }
    }

    #endregion

    #region Benchmarking

    private async Task<FunctionResult> ExecuteAsync(Func<Task<FunctionResult>> action)
    {
        var stopwatch = Stopwatch.StartNew();

        var result = await action();

        stopwatch.Stop();

        Console.WriteLine($@"Elapsed Time: {stopwatch.Elapsed:hh\:mm\:ss\.FFF}");

        return result;
    }

    #endregion
}
