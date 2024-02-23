// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.Connectors.HuggingFace.UnitTests;

public class HuggingFaceKernelBuilderExtensionsTests
{
    [Fact]
    public void AddHuggingFaceTextGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddHuggingFaceTextGeneration("model");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextGenerationService>(service);
    }

    [Fact]
    public void AddHuggingFaceTextGenerationToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddHuggingFaceTextGeneration("model");

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextGenerationService>();

        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextGenerationService>(service);
    }

    [Fact]
    public void AddHuggingFaceTextEmbeddingGenerationCreatesService()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddHuggingFaceTextEmbeddingGeneration("model");

        var kernel = builder.Build();
        var service = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(kernel);
        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextEmbeddingGenerationService>(service);
    }

    [Fact]
    public void AddHuggingFaceTextEmbeddingsGenerationToServiceCollection()
    {
        var services = new ServiceCollection();
        services.AddHuggingFaceTextEmbeddingGeneration("model");

        var serviceProvider = services.BuildServiceProvider();
        var service = serviceProvider.GetRequiredService<ITextEmbeddingGenerationService>();

        Assert.NotNull(service);
        Assert.IsType<HuggingFaceTextEmbeddingGenerationService>(service);
    }
}
