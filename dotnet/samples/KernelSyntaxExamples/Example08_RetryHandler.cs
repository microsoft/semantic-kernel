// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.Core;
using Microsoft.SemanticKernel.Reliability.Basic;
using Polly;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example08_RetryHandler
{
    public static async Task RunAsync()
    {
        await DefaultNoRetry();

        await ReliabilityBasicExtension();

        await ReliabilityPollyExtension();

        await CustomHandler();
    }

    private static async Task DefaultNoRetry()
    {
        InfoLogger.Logger.LogInformation("============================== Kernel default behavior: No Retry ==============================");
        var kernel = InitializeKernelBuilder()
            .Build();

        await ImportAndExecuteSkillAsync(kernel);
    }

    private static async Task ReliabilityBasicExtension()
    {
        InfoLogger.Logger.LogInformation("============================== Using Reliability.Basic extension ==============================");
        var retryConfig = new BasicRetryConfig
        {
            MaxRetryCount = 3,
            UseExponentialBackoff = true,
        };
        retryConfig.RetryableStatusCodes.Add(HttpStatusCode.Unauthorized);

        var kernel = InitializeKernelBuilder()
            .WithRetryBasic(retryConfig)
            .Build();

        await ImportAndExecuteSkillAsync(kernel);
    }

    private static async Task ReliabilityPollyExtension()
    {
        InfoLogger.Logger.LogInformation("============================== Using Reliability.Polly extension ==============================");
        var kernel = InitializeKernelBuilder()
            .WithRetryPolly(GetPollyPolicy(InfoLogger.LoggerFactory))
            .Build();

        await ImportAndExecuteSkillAsync(kernel);
    }

    private static async Task CustomHandler()
    {
        InfoLogger.Logger.LogInformation("============================== Using a Custom Http Handler ==============================");
        var kernel = InitializeKernelBuilder()
                        .WithHttpHandlerFactory(new MyCustomHandlerFactory())
                        .Build();

        await ImportAndExecuteSkillAsync(kernel);
    }

    private static KernelBuilder InitializeKernelBuilder()
    {
        return Kernel.Builder
                    .WithLoggerFactory(InfoLogger.LoggerFactory)
                    // OpenAI settings - you can set the OpenAI.ApiKey to an invalid value to see the retry policy in play
                    .WithOpenAIChatCompletionService(TestConfiguration.OpenAI.ChatModelId, "BAD_KEY");
    }

    private static AsyncPolicy<HttpResponseMessage> GetPollyPolicy(ILoggerFactory? logger)
    {
        // Handle 429 and 401 errors
        // Typically 401 would not be something we retry but for demonstration
        // purposes we are doing so as it's easy to trigger when using an invalid key.
        const int tooManyRequests = 429;
        const int unauthorized = 401;

        return Policy
            .HandleResult<HttpResponseMessage>(response =>
                (int)response.StatusCode is tooManyRequests or unauthorized)
            .WaitAndRetryAsync(new[]
                {
                    TimeSpan.FromSeconds(2),
                    TimeSpan.FromSeconds(4),
                    TimeSpan.FromSeconds(8)
                },
                (outcome, timespan, retryCount, _)
                    => InfoLogger.Logger.LogWarning("Error executing action [attempt {RetryCount} of 3], pausing {PausingMilliseconds}ms. Outcome: {StatusCode}",
                        retryCount,
                        timespan.TotalMilliseconds,
                        outcome.Result.StatusCode));
    }

    private static async Task ImportAndExecuteSkillAsync(IKernel kernel)
    {
        // Load semantic skill defined with prompt templates
        string folder = RepoFiles.SampleSkillsPath();

        kernel.ImportSkill(new TimePlugin(), "time");

        var qaSkill = kernel.ImportSemanticSkillFromDirectory(
            folder,
            "QASkill");

        var question = "How popular is Polly library?";

        InfoLogger.Logger.LogInformation("Question: {0}", question);
        // To see the retry policy in play, you can set the OpenAI.ApiKey to an invalid value
        var answer = await kernel.RunAsync(question, qaSkill["Question"]);
        InfoLogger.Logger.LogInformation("Answer: {0}", answer);
    }

    // Basic custom retry handler factory
    public sealed class MyCustomHandlerFactory : HttpHandlerFactory<MyCustomHandler>
    {
    }

    // Basic custom empty retry handler
    public sealed class MyCustomHandler : DelegatingHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Your custom http handling implementation

            throw new NotImplementedException();
        }
    }

    private static class InfoLogger
    {
        internal static ILogger Logger => LoggerFactory.CreateLogger("Example08_RetryHandler");
        internal static ILoggerFactory LoggerFactory => s_loggerFactory.Value;
        private static readonly Lazy<ILoggerFactory> s_loggerFactory = new(LogBuilder);

        private static ILoggerFactory LogBuilder()
        {
            return Microsoft.Extensions.Logging.LoggerFactory.Create(builder =>
            {
                builder.SetMinimumLevel(LogLevel.Information);
                builder.AddFilter("Microsoft", LogLevel.Information);
                builder.AddFilter("Microsoft.SemanticKernel", LogLevel.Critical);
                builder.AddFilter("Microsoft.SemanticKernel.Reliability", LogLevel.Information);
                builder.AddFilter("System", LogLevel.Information);

                builder.AddConsole();
            });
        }
    }
}
