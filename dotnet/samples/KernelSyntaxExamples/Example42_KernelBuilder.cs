// Copyright (c) Microsoft. All rights reserved.

// ==========================================================================================================
// The easier way to instantiate the Semantic Kernel is to use KernelBuilder.
// You can access the builder using new KernelBuilder().

#pragma warning disable CA1852

using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Plugins.Memory;
using Microsoft.SemanticKernel.Services;

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
        Kernel kernel1 = new KernelBuilder().Build();
#pragma warning restore CA1852 // Seal internal types

        Kernel kernel2 = new KernelBuilder().Build();

        // ==========================================================================================================
        // new KernelBuilder() returns a new builder instance, in case you want to configure the builder differently.
        // The following are 3 distinct builder instances.

        var builder1 = new KernelBuilder();

        var builder2 = new KernelBuilder();

        var builder3 = new KernelBuilder();

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
        var textEmbeddingGenerator = new AzureOpenAITextEmbeddingGeneration(
            deploymentName: azureOpenAIEmbeddingDeployment,
            endpoint: azureOpenAIEndpoint,
            apiKey: azureOpenAIKey,
            loggerFactory: loggerFactory);

        var memory = new SemanticTextMemory(memoryStorage, textEmbeddingGenerator);
        var plugins = new KernelPluginCollection();

        using var httpClient = new HttpClient();
        var aiServices = new AIServiceCollection();
        ITextCompletion Factory() => new AzureOpenAIChatCompletion(
            deploymentName: azureOpenAIChatCompletionDeployment,
            endpoint: azureOpenAIEndpoint,
            apiKey: azureOpenAIKey,
            httpClient: httpClient,
            loggerFactory: loggerFactory);
        aiServices.SetService("foo", Factory);
        IAIServiceProvider aiServiceProvider = aiServices.Build();

        // Create kernel manually injecting all the dependencies
        var kernel3 = new Kernel(aiServiceProvider, plugins, httpClient: httpClient, loggerFactory: loggerFactory);

        // ==========================================================================================================
        // The kernel builder purpose is to simplify this process, automating how dependencies
        // are connected, still allowing to customize parts of the composition.

        // ==========================================================================================================
        // The AI services are defined with the builder

        var kernel7 = new KernelBuilder()
            .WithAzureOpenAIChatCompletionService(
                deploymentName: azureOpenAIChatCompletionDeployment,
                endpoint: azureOpenAIEndpoint,
                apiKey: azureOpenAIKey,
                setAsDefault: true)
            .Build();

        return Task.CompletedTask;
    }
}
