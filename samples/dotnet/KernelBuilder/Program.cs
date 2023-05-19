// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using either Kernel.Builder or KernelBuilder.

#pragma warning disable CA1852
#pragma warning disable CA1050

using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

IKernel kernel1 = KernelBuilder.Create();

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
var textEmbeddingGenerator = new AzureTextEmbeddingGeneration("modelId", "https://...", "apiKey", logger: logger);
var memory = new SemanticTextMemory(memoryStorage, textEmbeddingGenerator);
var skills = new SkillCollection();
var templateEngine = new PromptTemplateEngine(logger);
var config = new KernelConfig();
var httpHandler = new DefaultHttpRetryHandler(new HttpRetryConfig(), logger);
var httpClient = new HttpClient(httpHandler);
ITextCompletion Factory(IKernel kernel) => new AzureTextCompletion("deploymentName", "https://...", "apiKey", httpClient, logger);
config.AddTextCompletionService(Factory);

// Create kernel manually injecting all the dependencies
var kernel3 = new Kernel(skills, templateEngine, memory, config, logger);

// ==========================================================================================================
// The kernel builder purpose is to simplify this process, automating how dependencies
// are connected, still allowing to customize parts of the composition.

// Example: how to use a custom memory and configure Azure OpenAI
var kernel4 = Kernel.Builder
    .WithLogger(NullLogger.Instance)
    .WithMemory(memory)
    .Configure(c =>
    {
        c.AddAzureTextCompletionService("deploymentName", "https://...", "apiKey");
    })
    .Build();

// Example: how to use a custom memory storage and custom embedding generator
var kernel5 = Kernel.Builder
    .WithLogger(NullLogger.Instance)
    .WithMemoryStorageAndTextEmbeddingGeneration(memoryStorage, textEmbeddingGenerator)
    .Build();

// Example: how to use a custom memory storage
var kernel6 = Kernel.Builder
    .WithLogger(NullLogger.Instance)
    .WithMemoryStorage(memoryStorage) // Custom memory storage
    .Configure(c =>
    {
        // This will be used when using AI completions
        c.AddAzureTextCompletionService("completionDeploymentName", "https://...", "apiKey");

        // This will be used when indexing memory records
        c.AddAzureTextEmbeddingGenerationService("embeddingsDeploymentName", "https://...", "apiKey", serviceId: "myName3");
    })
    .Build();

// ==========================================================================================================
// The kernel configuration can be defined with the builder, but can also be managed
// when the kernel instance is already created.

var kernel7 = Kernel.Builder
    .Configure(c =>
    {
        c.AddAzureTextCompletionService("completionDeploymentName", "https://...", "apiKey");
    })
    .Configure(c =>
    {
        c.SetDefaultTextEmbeddingGenerationService("myName3");
    })
    .Build();

kernel7.Config
    .AddAzureTextEmbeddingGenerationService("embeddingsDeploymentName1", "https://...", "apiKey", serviceId: "myName2")
    .AddAzureTextEmbeddingGenerationService("embeddingsDeploymentName2", "https://...", "apiKey", serviceId: "myName3")
    .AddOpenAITextCompletionService("text-davinci-003", "sk-...");

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

// Example of a basic custom retry handler
public class RetryThreeTimesFactory : IDelegatingHandlerFactory
{
    public DelegatingHandler Create(ILogger? log)
    {
        return new RetryThreeTimes(log);
    }
}

public class RetryThreeTimes : DelegatingHandler
{
    private readonly AsyncRetryPolicy _policy;

    public RetryThreeTimes(ILogger? log = null)
    {
        this._policy = GetPolicy(log ?? NullLogger.Instance);
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        return await this._policy.ExecuteAsync(async () =>
        {
            var response = await base.SendAsync(request, cancellationToken);
            return response;
        });
    }

    private static AsyncRetryPolicy GetPolicy(ILogger log)
    {
        return Policy
            .Handle<AIException>(ex => ex.ErrorCode == AIException.ErrorCodes.Throttling)
            .WaitAndRetryAsync(new[]
                {
                    TimeSpan.FromSeconds(2),
                    TimeSpan.FromSeconds(4),
                    TimeSpan.FromSeconds(8)
                },
                (ex, timespan, retryCount, _) => log.LogWarning(ex,
                    "Error executing action [attempt {0} of 3], pausing {1}ms",
                    retryCount, timespan.TotalMilliseconds));
    }
}
