// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

#pragma warning disable CA1031 // Do not catch general exception types
#pragma warning disable CA2000 // Dispose objects before losing scope

public static class Example08_RetryHandler
{
    public static async Task RunAsync()
    {
        // Create a Kernel with the HttpClient
        var kernel = new KernelBuilder().ConfigureServices(c =>
        {
            c.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
            c.ConfigureHttpClientDefaults(c =>
            {
                // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
                c.AddStandardResilienceHandler().Configure(o =>
                {
                    o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
                });
            });
            c.AddOpenAIChatCompletion("gpt-4", "BAD_KEY"); // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
        }).Build();

        var logger = kernel.LoggerFactory.CreateLogger(typeof(Example08_RetryHandler));

        const string Question = "How popular is Polly library?";
        logger.LogInformation("Question: {Question}", Question);
        try
        {
            logger.LogInformation("Answer: {Result}", await kernel.InvokePromptAsync(Question));
        }
        catch (Exception ex)
        {
            logger.LogInformation("Error: {Message}", ex.Message);
        }
    }
}
