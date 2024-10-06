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
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Polly;
using Polly.Retry;

// ReSharper disable once InconsistentNaming
public static class Example42_KernelBuilder
{
    public static Task RunAsync()
    {
        string azureOpenAIKey = TestConfiguration.AzureOpenAI.ApiKey;
        string azureOpenAIEndpoint = TestConfiguration.AzureOpenAI.Endpoint;
        string azureOpenAITextCompletionDeployment = TestConfiguration.AzureOpenAI.DeploymentName;
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

        // Manually setup all the dependencies used internally by the kernel
        var logger = NullLogger.Instance;
        var memoryStorage = new VolatileMemoryStore();
        var textEmbeddingGenerator = new AzureTextEmbeddingGeneration(
            modelId: azureOpenAIEmbeddingDeployment,
            endpoint: azureOpenAIEndpoint,
            apiKey: azureOpenAIKey,
            logger: logger);
        using var memory = new SemanticTextMemory(memoryStorage, textEmbeddingGenerator);
        var skills = new SkillCollection();
        var templateEngine = new PromptTemplateEngine(logger);
        var kernelConfig = new KernelConfig();

        using var httpHandler = new DefaultHttpRetryHandler(new HttpRetryConfig(), logger);
        using var httpClient = new HttpClient(httpHandler);
        var aiServices = new AIServiceCollection();
        ITextCompletion Factory() => new AzureTextCompletion(
            modelId: azureOpenAITextCompletionDeployment,
            endpoint: azureOpenAIEndpoint,
            apiKey: azureOpenAIKey,
            httpClient,
            logger);
        aiServices.SetService("foo", Factory);
        IAIServiceProvider aiServiceProvider = aiServices.Build();

        // Create kernel manually injecting all the dependencies
        using var kernel3 = new Kernel(skills, aiServiceProvider, templateEngine, memory, kernelConfig, logger);

        // ==========================================================================================================
        // The kernel builder purpose is to simplify this process, automating how dependencies
        // are connected, still allowing to customize parts of the composition.

        // Example: how to use a custom memory and configure Azure OpenAI
        var kernel4 = Kernel.Builder
            .WithLogger(NullLogger.Instance)
            .WithMemory(memory)
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAITextCompletionDeployment,
                endpoint: azureOpenAIEndpoint,
                apiKey: azureOpenAIKey)
            .Build();

        // Example: how to use a custom memory storage
        var kernel6 = Kernel.Builder
            .WithLogger(NullLogger.Instance)
            .WithMemoryStorage(memoryStorage) // Custom memory storage
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAITextCompletionDeployment,
                endpoint: azureOpenAIEndpoint,
                apiKey: azureOpenAIKey) // This will be used when using AI completions
            .WithAzureTextEmbeddingGenerationService(
                deploymentName: azureOpenAIEmbeddingDeployment,
                endpoint: azureOpenAIEndpoint,
                apiKey: azureOpenAIKey) // This will be used when indexing memory records
            .Build();

        // ==========================================================================================================
        // The AI services are defined with the builder

        var kernel7 = Kernel.Builder
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAITextCompletionDeployment,
                endpoint: azureOpenAIEndpoint,
                apiKey: azureOpenAIKey,
                setAsDefault: true)
            .Build();

        // ==========================================================================================================
        // When invoking AI, by default the kernel will retry on transient errors, such as throttling and timeouts.
        // The default behavior can be configured or a custom retry handler can be injected that will apply to all
        // AI requests (when using the kernel).

        var kernel8 = Kernel.Builder
            .Configure(c => c.SetDefaultHttpRetryConfig(new HttpRetryConfig
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true,
                //  MinRetryDelay = TimeSpan.FromSeconds(2),
                //  MaxRetryDelay = TimeSpan.FromSeconds(8),
                //  MaxTotalRetryTime = TimeSpan.FromSeconds(30),
                //  RetryableStatusCodes = new[] { HttpStatusCode.TooManyRequests, HttpStatusCode.RequestTimeout },
                //  RetryableExceptions = new[] { typeof(HttpRequestException) }
            }))
            .Build();

        var kernel9 = Kernel.Builder
            .Configure(c => c.SetHttpRetryHandlerFactory(new NullHttpRetryHandlerFactory()))
            .Build();

        var kernel10 = Kernel.Builder.WithRetryHandlerFactory(new RetryThreeTimesFactory()).Build();

        return Task.CompletedTask;
    }

    // Example of a basic custom retry handler
    public class RetryThreeTimesFactory : IDelegatingHandlerFactory
    {
        public DelegatingHandler Create(ILogger? logger)
        {
            return new RetryThreeTimes(logger);
        }
    }

    public class RetryThreeTimes : DelegatingHandler
    {
        private readonly AsyncRetryPolicy _policy;

        public RetryThreeTimes(ILogger? logger = null)
        {
            this._policy = GetPolicy(logger ?? NullLogger.Instance);
        }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return await this._policy.ExecuteAsync(async () =>
            {
                var response = await base.SendAsync(request, cancellationToken);
                return response;
            });
        }

        private static AsyncRetryPolicy GetPolicy(ILogger logger)
        {
            return Policy
                .Handle<HttpOperationException>(ex => ex.StatusCode == System.Net.HttpStatusCode.TooManyRequests)
                .WaitAndRetryAsync(new[]
                    {
                        TimeSpan.FromSeconds(2),
                        TimeSpan.FromSeconds(4),
                        TimeSpan.FromSeconds(8)
                    },
                    (ex, timespan, retryCount, _) => logger.LogWarning(ex,
                        "Error executing action [attempt {0} of 3], pausing {1}ms",
                        retryCount, timespan.TotalMilliseconds));
        }
// You can access the builder using Kernel.CreateBuilder().

using System.Diagnostics;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example42_KernelBuilder : BaseTest
{
    [Fact]
    public void BuildKernelWithAzureChatCompletion()
    {
        // KernelBuilder provides a simple way to configure a Kernel. This constructs a kernel
        // with logging and an Azure OpenAI chat completion service configured.
        Kernel kernel1 = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId)
            .Build();
    }

    [Fact]
    public void BuildKernelUsingServiceCollection()
    {
        // For greater flexibility and to incorporate arbitrary services, KernelBuilder.Services
        // provides direct access to an underlying IServiceCollection.
        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information))
            .AddHttpClient()
            .AddAzureOpenAIChatCompletion(
                deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
                endpoint: TestConfiguration.AzureOpenAI.Endpoint,
                apiKey: TestConfiguration.AzureOpenAI.ApiKey,
                modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        Kernel kernel2 = builder.Build();
    }

    [Fact]
    public void BuildKernelWithPlugins()
    {
        // Plugins may also be configured via the corresponding Plugins property.
        var builder = Kernel.CreateBuilder();
        builder.Plugins.AddFromType<HttpPlugin>();
        Kernel kernel3 = builder.Build();
    }

    [Fact]
    public void BuildKernelUsingServiceProvider()
    {
        // Every call to KernelBuilder.Build creates a new Kernel instance, with a new service provider
        // and a new plugin collection.
        var builder = Kernel.CreateBuilder();
        Debug.Assert(!ReferenceEquals(builder.Build(), builder.Build()));

        // KernelBuilder provides a convenient API for creating Kernel instances. However, it is just a
        // wrapper around a service collection, ultimately constructing a Kernel
        // using the public constructor that's available for anyone to use directly if desired.
        var services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        Kernel kernel4 = new(services.BuildServiceProvider());

        // Kernels can also be constructed and resolved via such a dependency injection container.
        services.AddTransient<Kernel>();
        Kernel kernel5 = services.BuildServiceProvider().GetRequiredService<Kernel>();
    }

    [Fact]
    public void BuildKernelUsingServiceCollectionExtension()
    {
        // In fact, the AddKernel method exists to simplify this, registering a singleton KernelPluginCollection
        // that can be populated automatically with all IKernelPlugins registered in the collection, and a
        // transient Kernel that can then automatically be constructed from the service provider and resulting
        // plugins collection.
        var services = new ServiceCollection();
        services.AddLogging(c => c.AddConsole().SetMinimumLevel(LogLevel.Information));
        services.AddHttpClient();
        services.AddKernel().AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            endpoint: TestConfiguration.AzureOpenAI.Endpoint,
            apiKey: TestConfiguration.AzureOpenAI.ApiKey,
            modelId: TestConfiguration.AzureOpenAI.ChatModelId);
        services.AddSingleton<KernelPlugin>(sp => KernelPluginFactory.CreateFromType<TimePlugin>(serviceProvider: sp));
        services.AddSingleton<KernelPlugin>(sp => KernelPluginFactory.CreateFromType<HttpPlugin>(serviceProvider: sp));
        Kernel kernel6 = services.BuildServiceProvider().GetRequiredService<Kernel>();
    }

    public Example42_KernelBuilder(ITestOutputHelper output) : base(output)
    {
    }
}
