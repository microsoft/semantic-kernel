// Copyright (c) Microsoft. All rights reserved.

using System.ClientModel;
using System.Net;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Filtering;

/// <summary>
/// This example shows how to perform retry with filter and switch to another model as a fallback.
/// </summary>
public class RetryWithFilters(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ChangeModelAndRetryAsync()
    {
        // Default and fallback models for demonstration purposes
        const string DefaultModelId = "gpt-4";
        const string FallbackModelId = "gpt-3.5-turbo-1106";

        var builder = Kernel.CreateBuilder();

        // Add OpenAI chat completion service with an invalid API key to force a 401 Unauthorized response
        builder.AddOpenAIChatCompletion(modelId: DefaultModelId, apiKey: "invalid_key");

        // Add OpenAI chat completion service with valid configuration as a fallback
        builder.AddOpenAIChatCompletion(modelId: FallbackModelId, apiKey: TestConfiguration.OpenAI.ApiKey);

        // Add retry filter
        builder.Services.AddSingleton<IFunctionInvocationFilter>(new RetryFilter(FallbackModelId));

        // Build kernel
        var kernel = builder.Build();

        // Initially, use "GPT-4" with invalid API key to simulate exception
        var executionSettings = new OpenAIPromptExecutionSettings { ModelId = DefaultModelId, MaxTokens = 20 };

        var result = await kernel.InvokePromptAsync("Hi, can you help me today?", new(executionSettings));

        Console.WriteLine(result);

        // Output: Of course! I'll do my best to help you. What do you need assistance with?
    }

    [Fact]
    public async Task ChangeModelAndRetryStreaming()
    {
        // Default and fallback models for demonstration purposes
        const string DefaultModelId = "gpt-4";
        const string FallbackModelId = "gpt-3.5-turbo-1106";

        var builder = Kernel.CreateBuilder();

        // Add OpenAI chat completion service with an invalid API key to force a 401 Unauthorized response
        builder.AddOpenAIChatCompletion(modelId: DefaultModelId, apiKey: "invalid_key");

        // Add OpenAI chat completion service with valid configuration as a fallback
        builder.AddOpenAIChatCompletion(modelId: FallbackModelId, apiKey: TestConfiguration.OpenAI.ApiKey);

        // Add retry filter
        builder.Services.AddSingleton<IFunctionInvocationFilter>(new StreamingRetryFilter(FallbackModelId));

        // Build kernel
        var kernel = builder.Build();

        // Initially, use "GPT-4" with invalid API key to simulate exception
        var executionSettings = new OpenAIPromptExecutionSettings { ModelId = DefaultModelId, MaxTokens = 20 };

        await foreach (var result in kernel.InvokePromptStreamingAsync("Hi, can you help me today?", new(executionSettings)))
        {
            Console.Write(result);
        }
    }

    /// <summary>
    /// Filter to change the model and perform retry in case of exception.
    /// </summary>
    private sealed class RetryFilter(string fallbackModelId) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            try
            {
                // Try to invoke function
                await next(context);
            }
            // Catch specific exception
            catch (HttpOperationException exception) when (exception.StatusCode == HttpStatusCode.Unauthorized)
            {
                // Get current execution settings
                PromptExecutionSettings executionSettings = context.Arguments.ExecutionSettings![PromptExecutionSettings.DefaultServiceId];

                // Override settings with fallback model id
                executionSettings.ModelId = fallbackModelId;

                // Try to invoke function again
                await next(context);
            }
        }
    }

    /// <summary>
    /// Filter to change the model and perform retry in case of exception.
    /// </summary>
    private sealed class StreamingRetryFilter(string fallbackModelId) : IFunctionInvocationFilter
    {
        public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
        {
            // Try to invoke function
            await next(context);

            var enumerable = context.Result.GetValue<IAsyncEnumerable<StreamingKernelContent>>()!;
            context.Result = new FunctionResult(context.Result, this.DeferredStreamingRetryResult(enumerable, context, next));
        }

        private async IAsyncEnumerable<StreamingKernelContent> DeferredStreamingRetryResult(IAsyncEnumerable<StreamingKernelContent> results, FunctionInvocationContext context, Func<FunctionInvocationContext, Task> retry)
        {
            // I need to manually enumerate the results to catch the exception.
            var enumerator = results.GetAsyncEnumerator();

            while (true)
            {
                try
                {
                    if (!await enumerator.MoveNextAsync())
                    {
                        break;
                    }
                }
                catch (ClientResultException exception) when (exception.Status == (int)HttpStatusCode.Unauthorized)
                {
                    // In a scenario where the streaming already started and it was interrupted by an exception,
                    // would be advisable some extra logic to handle any update necessary in the caller side before the retrial starts

                    // If any exception is thrown, get current execution settings to override settings with fallback model id
                    PromptExecutionSettings executionSettings = context.Arguments.ExecutionSettings![PromptExecutionSettings.DefaultServiceId];

                    // Override settings with fallback model id
                    executionSettings.ModelId = fallbackModelId;

                    // Try to invoke function again
                    await retry(context);

                    // Set the new result enumerator
                    enumerator = context.Result.GetValue<IAsyncEnumerable<StreamingKernelContent>>()!.GetAsyncEnumerator();

                    // Retry the enumeration
                    continue;
                }

                yield return enumerator.Current;
            }
        }
    }
}
