// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Polly;

#pragma warning disable CA1031 // Do not catch general exception types
#pragma warning disable CA2000 // Dispose objects before losing scope

public static class Example08_RetryHandler
{
    public static async Task RunAsync()
    {
        var loggingFactory = LoggerFactory.Create(b => b.AddConsole().SetMinimumLevel(LogLevel.Information));
        var logger = loggingFactory.CreateLogger(typeof(Example08_RetryHandler));

        // Create a retry policy with Polly
        var policy = Policy
            .HandleResult<HttpResponseMessage>(response => response.StatusCode is HttpStatusCode.TooManyRequests or HttpStatusCode.Unauthorized)
            .WaitAndRetryAsync(
                new[] { TimeSpan.FromSeconds(2), TimeSpan.FromSeconds(4), TimeSpan.FromSeconds(8) },
                (outcome, timespan, retryCount, _) => logger.LogWarning("Error executing action [attempt {RetryCount} of 3], pausing {PausingMilliseconds}ms. Outcome: {StatusCode}",
                    retryCount, timespan.TotalMilliseconds, outcome.Result.StatusCode));

        // Create an HttpClient with the retry policy
        var client = new HttpClient(new PolicyHttpMessageHandler(policy) { InnerHandler = new SocketsHttpHandler() });

        // Create a Kernel with the HttpClient
        var kernel = new KernelBuilder()
            .WithLoggerFactory(loggingFactory)
            .WithHttpClient(client)
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, "BAD_KEY") // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
            .Build();

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
