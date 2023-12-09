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

/*
 * This example shows how to use a retry handler within a Semantic Kernel
 */
public static class Example08_RetryHandler
{
    public static async Task RunAsync()
    {
        // Create a Kernel with the HttpClient
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        builder.Services.ConfigureHttpClientDefaults(c =>
        {
            // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
            });
        });
        builder.Services.AddOpenAIChatCompletion("gpt-4", "BAD_KEY"); // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
        Kernel kernel = builder.Build();

        var logger = kernel.LoggerFactory.CreateLogger(typeof(Example08_RetryHandler));

        const string Question = "How popular is the Polly library?";
        logger.LogInformation("Question: {Question}", Question);

        // The call to OpenAI will fail and be retried a few times before eventually failing.
        // Retrying can overcome transient problems and thus improves resiliency.
        try
        {
            // The InvokePromptAsync call will issue a request to OpenAI with an invalid API key.
            // That will cause the request to fail with an HTTP status code 401. As the resilience
            // handler is configured to retry on 401s, it'll reissue the request, and will do so
            // multiple times until it hits the default retry limit, at which point this operation
            // will throw an exception in response to the failure. All of the retries will be visible
            // in the logging out to the console.
            logger.LogInformation("Answer: {Result}", await kernel.InvokePromptAsync(Question));
        }
        catch (Exception ex)
        {
            logger.LogInformation("Error: {Message}", ex.Message);
        }
    }
}
