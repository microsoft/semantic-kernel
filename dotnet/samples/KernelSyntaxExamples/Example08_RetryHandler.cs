// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Config;
using Microsoft.SemanticKernel.Reliability.Polly;
using Microsoft.SemanticKernel.Skills.Core;
using Reliability;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example08_RetryHandler
{
    public static async Task RunAsync()
    {
        var kernel = InitializeKernel();
        var retryHandlerFactory = new RetryThreeTimesWithBackoffFactory();

        InfoLogger.Logger.LogInformation("============================== RetryThreeTimesWithBackoff ==============================");
        await RunRetryPolicyAsync(kernel, retryHandlerFactory);

        InfoLogger.Logger.LogInformation("========================= RetryThreeTimesWithRetryAfterBackoff =========================");
        await RunRetryPolicyBuilderAsync<RetryThreeTimesWithRetryAfterBackoffFactory>();

        InfoLogger.Logger.LogInformation("==================================== NoRetryPolicy =====================================");
        await RunRetryPolicyBuilderAsync<NullHttpHandlerFactory>();

        InfoLogger.Logger.LogInformation("=============================== DefaultHttpRetryHandler ================================");
        await RunRetryHandlerConfigAsync(new() { MaxRetryCount = 3, UseExponentialBackoff = true });

        InfoLogger.Logger.LogInformation("======= DefaultHttpRetryConfig [MaxRetryCount = 3, UseExponentialBackoff = true] =======");
        await RunRetryHandlerConfigAsync(new() { MaxRetryCount = 3, UseExponentialBackoff = true });
    }

    private static async Task RunRetryHandlerConfigAsync(HttpRetryConfig? httpConfig = null)
    {
        var kernelBuilder = Kernel.Builder.WithLoggerFactory(InfoLogger.LoggerFactory);
        if (httpConfig != null)
        {
            // Add 401 to the list of retryable status codes
            // Typically 401 would not be something we retry but for demonstration
            // purposes we are doing so as it's easy to trigger when using an invalid key.
            httpConfig.RetryableStatusCodes.Add(HttpStatusCode.Unauthorized);

            kernelBuilder = kernelBuilder.Configure(c => c.SetHttpRetryConfig(httpConfig));
        }

        // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
        kernelBuilder = kernelBuilder.WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, "BAD_KEY");

        var kernel = kernelBuilder.Build();

        await ImportAndExecuteSkillAsync(kernel);
    }

    private static IKernel InitializeKernel()
    {
        var kernel = Kernel.Builder
            .WithLoggerFactory(InfoLogger.LoggerFactory)
            // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, "BAD_KEY")
            .Build();

        return kernel;
    }

    private static async Task RunRetryPolicyAsync(IKernel kernel, IDelegatingHandlerFactory retryHandlerFactory)
    {
        kernel.Config.SetHttpHandlerFactory(retryHandlerFactory);
        await ImportAndExecuteSkillAsync(kernel);
    }

    private static async Task RunRetryPolicyBuilderAsync<T>()
    {
        var kernel = Kernel.Builder.WithLoggerFactory(InfoLogger.LoggerFactory)
            .WithHttpHandlerFactory((Activator.CreateInstance(typeof(T)) as IDelegatingHandlerFactory)!)
            // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
            .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, "BAD_KEY")
            .Build();

        await ImportAndExecuteSkillAsync(kernel);
    }

    private static async Task ImportAndExecuteSkillAsync(IKernel kernel)
    {
        // Load semantic skill defined with prompt templates
        string folder = RepoFiles.SampleSkillsPath();

        kernel.ImportSkill(new TimeSkill(), "time");

        var qaSkill = kernel.ImportSemanticSkillFromDirectory(
            folder,
            "QASkill");

        var question = "How popular is Polly library?";

        InfoLogger.Logger.LogInformation("Question: {0}", question);
        // To see the retry policy in play, you can set the OpenAI.ApiKey to an invalid value
        var answer = await kernel.RunAsync(question, qaSkill["Question"]);
        InfoLogger.Logger.LogInformation("Answer: {0}", answer);
    }

    private static class InfoLogger
    {
        internal static ILogger Logger => LoggerFactory.CreateLogger<object>();
        internal static ILoggerFactory LoggerFactory => s_loggerFactory.Value;
        private static readonly Lazy<ILoggerFactory> s_loggerFactory = new(LogBuilder);

        private static ILoggerFactory LogBuilder()
        {
            return Microsoft.Extensions.Logging.LoggerFactory.Create(builder =>
            {
                builder.SetMinimumLevel(LogLevel.Information);
                builder.AddFilter("Microsoft", LogLevel.Information);
                builder.AddFilter("System", LogLevel.Information);

                builder.AddConsole();
            });
        }
    }
}

/* Output:
info: object[0]
      ============================== RetryThreeTimesWithBackoff ==============================
info: object[0]
      Question: How popular is Polly library?
warn: object[0]
      Error executing action [attempt 1 of 3], pausing 2000ms. Outcome: Unauthorized
warn: object[0]
      Error executing action [attempt 2 of 3], pausing 4000ms. Outcome: Unauthorized
warn: object[0]
      Error executing action [attempt 3 of 3], pausing 8000ms. Outcome: Unauthorized
fail: object[0]
      Function call fail during pipeline step 0: QASkill.Question
info: object[0]
      Answer: Error: AccessDenied: The request is not authorized, HTTP status: Unauthorized
info: object[0]
      ========================= RetryThreeTimesWithRetryAfterBackoff =========================
info: object[0]
      Question: How popular is Polly library?
warn: object[0]
      Error executing action [attempt 1 of 3], pausing 2000ms. Outcome: Unauthorized
warn: object[0]
      Error executing action [attempt 2 of 3], pausing 2000ms. Outcome: Unauthorized
warn: object[0]
      Error executing action [attempt 3 of 3], pausing 2000ms. Outcome: Unauthorized
fail: object[0]
      Function call fail during pipeline step 0: QASkill.Question
info: object[0]
      Answer: Error: AccessDenied: The request is not authorized, HTTP status: Unauthorized
info: object[0]
      ==================================== NoRetryPolicy =====================================
info: object[0]
      Question: How popular is Polly library?
fail: object[0]
      Function call fail during pipeline step 0: QASkill.Question
info: object[0]
      Answer: Error: AccessDenied: The request is not authorized, HTTP status: Unauthorized
info: object[0]
      =============================== DefaultHttpRetryHandler ================================
info: object[0]
      Question: How popular is Polly library?
warn: object[0]
      Error executing action [attempt 1 of 3]. Reason: Unauthorized. Will retry after 2000ms
warn: object[0]
      Error executing action [attempt 2 of 3]. Reason: Unauthorized. Will retry after 4000ms
warn: object[0]
      Error executing action [attempt 3 of 3]. Reason: Unauthorized. Will retry after 8000ms
fail: object[0]
      Error executing request, max retry count reached. Reason: Unauthorized
fail: object[0]
      Function call fail during pipeline step 0: QASkill.Question
info: object[0]
      Answer: Error: AccessDenied: The request is not authorized, HTTP status: Unauthorized
info: object[0]
      ======= DefaultHttpRetryConfig [MaxRetryCount = 3, UseExponentialBackoff = true] =======
info: object[0]
      Question: How popular is Polly library?
warn: object[0]
      Error executing action [attempt 1 of 3]. Reason: Unauthorized. Will retry after 2000ms
warn: object[0]
      Error executing action [attempt 2 of 3]. Reason: Unauthorized. Will retry after 4000ms
warn: object[0]
      Error executing action [attempt 3 of 3]. Reason: Unauthorized. Will retry after 8000ms
fail: object[0]
      Error executing request, max retry count reached. Reason: Unauthorized
fail: object[0]
      Function call fail during pipeline step 0: QASkill.Question
info: object[0]
      Answer: Error: AccessDenied: The request is not authorized, HTTP status: Unauthorized
*/
