// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using either Kernel.Builder or KernelBuilder.

#pragma warning disable CA1852

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Reliability.Basic;
using Microsoft.SemanticKernel.Reliability.Polly;
using Microsoft.SemanticKernel.Services;

using Microsoft.SemanticKernel.TemplateEngine.Prompt;
using Polly;
using Polly.Retry;

// ReSharper disable once InconsistentNaming
public static class Example42_KernelBuilder
{
    public static Task RunAsync()
    {
        string azureOpenAIKey = TestConfiguration.AzureOpenAI.ApiKey;
        string azureOpenAIEndpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string azureOpenAIChatCompletionDeployment = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string azureOpenAIEmbeddingDeployment = TestConfiguration.AzureOpenAIEmbeddings.DeploymentName;

#pragma warning disable CA1852 // Seal internal types
        IKernel kernel1 = Kernel.Builder.Build();
#pragma warning restore CA1852 // Seal internal types

        IKernel kernel2 = Kernel.Builder.Build();

        // ==========================================================================================================
        // Kernel.Builder returns a new builder instance, in case you want to configure the builder differently.
        // The following are 3 distinct builder instances.

        var builder1 = new KernelBuilder();

        var builder2 = Kernel.Builder;

        var builder3 = Kernel.Builder;

        // ==========================================================================================================
        // A builder instance can create multiple kernel instances, e.g. in case you need
        // multiple kernels that share the same dependencies.

        var builderX = new KernelBuilder();

        var kernelX1 = builderX.Build();
        var kernelX2 = builderX.Build();
        var kernelX3 = builderX.Build();

        // ==========================================================================================================
        // Kernel instances can be created the usual way with "new", though the process requires particular
        // attention to how dependencies are wired together. Although the building blocks are available
        // to enable custom configurations, we highly recommend using KernelBuilder instead, to ensure
        // a correct dependency injection.

        // Manually setup all the dependencies to be used by the kernel
        var loggerFactory = NullLoggerFactory.Instance;
        var memoryStorage = new VolatileMemoryStore();
        var textEmbeddingGenerator = new AzureTextEmbeddingGeneration(
            modelId: azureOpenAIEmbeddingDeployment,
            endpoint: azureOpenAIEndpoint,
            apiKey: azureOpenAIKey,
            loggerFactory: loggerFactory);

        var memory = new SemanticTextMemory(memoryStorage, textEmbeddingGenerator);
        var plugins = new FunctionCollection();
        var templateEngine = new PromptTemplateEngine(loggerFactory);

        var httpHandlerFactory = BasicHttpRetryHandlerFactory.Instance;
        //var httpHandlerFactory = new PollyHttpRetryHandlerFactory( your policy );

        using var httpHandler = httpHandlerFactory.Create(loggerFactory);
        using var httpClient = new HttpClient(httpHandler);
        var aiServices = new AIServiceCollection();
        ITextCompletion Factory() => new AzureChatCompletion(
            modelId: azureOpenAIChatCompletionDeployment,
            endpoint: azureOpenAIEndpoint,
            apiKey: azureOpenAIKey,
            httpClient,
            loggerFactory);
        aiServices.SetService("foo", Factory);
        IAIServiceProvider aiServiceProvider = aiServices.Build();

        // Create kernel manually injecting all the dependencies
        using var kernel3 = new Kernel(plugins, aiServiceProvider, templateEngine, memory, httpHandlerFactory, loggerFactory);

        // ==========================================================================================================
        // The kernel builder purpose is to simplify this process, automating how dependencies
        // are connected, still allowing to customize parts of the composition.

        // ==========================================================================================================
        // The AI services are defined with the builder

        var kernel7 = Kernel.Builder
            .WithAzureChatCompletionService(
                deploymentName: azureOpenAIChatCompletionDeployment,
                endpoint: azureOpenAIEndpoint,
                apiKey: azureOpenAIKey,
                setAsDefault: true)
            .Build();

        // ==========================================================================================================
        // When invoking AI, by default the kernel will retry on transient errors, such as throttling and timeouts.
        // The default behavior can be configured or a custom retry handler can be injected that will apply to all
        // AI requests (when using the kernel).

        var kernel8 = Kernel.Builder.WithRetryBasic(
            new BasicRetryConfig
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                //  MinRetryDelay = TimeSpan.FromSeconds(2),
                //  MaxRetryDelay = TimeSpan.FromSeconds(8),
                //  MaxTotalRetryTime = TimeSpan.FromSeconds(30),
                //  RetryableStatusCodes = new[] { HttpStatusCode.TooManyRequests, HttpStatusCode.RequestTimeout },
                //  RetryableExceptions = new[] { typeof(HttpRequestException) }
            })
            .Build();

        var logger = loggerFactory.CreateLogger<PollyHttpRetryHandlerFactory>();
        var retryThreeTimesPolicy = Policy
            .Handle<HttpOperationException>(ex
                => ex.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            .WaitAndRetryAsync(new[]
                {
                    TimeSpan.FromSeconds(2),
                    TimeSpan.FromSeconds(4),
                    TimeSpan.FromSeconds(8)
                },
                (ex, timespan, retryCount, _)
                    => logger?.LogWarning(ex, "Error executing action [attempt {RetryCount} of 3], pausing {PausingMilliseconds}ms", retryCount, timespan.TotalMilliseconds));

        var kernel9 = Kernel.Builder.WithHttpHandlerFactory(new PollyHttpRetryHandlerFactory(retryThreeTimesPolicy)).Build();

        var kernel10 = Kernel.Builder.WithHttpHandlerFactory(new PollyRetryThreeTimesFactory()).Build();

        var kernel11 = Kernel.Builder.WithHttpHandlerFactory(new MyCustomHandlerFactory()).Build();

        return Task.CompletedTask;
    }

    // Example using the PollyHttpRetryHandler from Reliability.Polly extension
    public class PollyRetryThreeTimesFactory : HttpHandlerFactory<PollyHttpRetryHandler>
    {
        public override DelegatingHandler Create(ILoggerFactory? loggerFactory = null)
        {
            var logger = loggerFactory?.CreateLogger<PollyRetryThreeTimesFactory>();

            Activator.CreateInstance(typeof(PollyHttpRetryHandler), GetPolicy(logger), logger);
            return base.Create(loggerFactory);
        }

        private static AsyncRetryPolicy GetPolicy(ILogger? logger)
        {
            return Policy
            .Handle<HttpOperationException>(ex
                => ex.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
            .WaitAndRetryAsync(new[]
                {
                    TimeSpan.FromSeconds(2),
                    TimeSpan.FromSeconds(4),
                    TimeSpan.FromSeconds(8)
                },
                (ex, timespan, retryCount, _)
                    => logger?.LogWarning(ex, "Error executing action [attempt {RetryCount} of 3], pausing {PausingMilliseconds}ms",
                    retryCount,
                    timespan.TotalMilliseconds));
        }
    }

    // Basic custom retry handler factory
    public class MyCustomHandlerFactory : HttpHandlerFactory<MyCustomHandler>
    {
    }

    // Basic custom empty retry handler
    public class MyCustomHandler : DelegatingHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Your custom handler implementation

            throw new NotImplementedException();
        }
    }
}
